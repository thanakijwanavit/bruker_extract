import numpy as np
from struct import unpack_from
from .utils import find_all
from .opus_data import OpusData
from itertools import product


class NoAbsorbanceSpectra(Exception):
    pass


def opus_reader(filepath):
    with open(filepath, 'rb') as f:
        buff = f.read()

    # Reading all waves and spectras
    fxv_spc, spc, wavenumbers = read_all_spectras(buff)
    # Choose best ab spectra
    ab_spectra, ab_wavenumbers = choose_ab(fxv_spc, spc, wavenumbers)

    wave_num_abs_pair = reversed(zip(ab_wavenumbers, ab_spectra))

    meta = get_meta_data(buff)

    return OpusData(zip(*wave_num_abs_pair), meta=meta)


def choose_ab(fxv_spc, spc, wavenumbers):
    # Filtering interferograms - we don't need them
    which_ig = np.where(fxv_spc == 0)[0]
    not_ig = np.setdiff1d(range(len(fxv_spc)), which_ig)

    # Filtering single channel spectras - that's just guessing, but it works!
    ab = []
    for x in not_ig:
        if np.average(spc[x]) > 0.25:
            ab.append(x)
    if len(ab) > 1:
        spc_avg = map(lambda x: np.average(spc[x]), ab)
        max_avg_index = spc_avg.index(max(spc_avg))
        ab_p = ab[max_avg_index]
    elif len(ab) == 1:
        ab_p = ab[0]
    else:
        raise NoAbsorbanceSpectra()

    ab_spectra = spc[ab_p]
    ab_wavenumbers = wavenumbers[ab[0]]
    return ab_spectra, ab_wavenumbers


def keyword_positions(buff):
    end = np.array(list(find_all("END", buff))) + 12
    npt_all = np.array(list(find_all("NPT", buff))) + 8
    fxv_all = np.array(list(find_all("FXV", buff))) + 8
    lxv_all = np.array(list(find_all("LXV", buff))) + 8
    return end, npt_all, fxv_all, lxv_all


def filter_unpaired(fxv_all, lxv_all):
    if len(fxv_all) != len(lxv_all):
        prod = product(fxv_all, lxv_all)
        correct_adressess = zip(*filter(lambda d: (d[1] - d[0]) == 16, prod))
        fxv_all = np.array(correct_adressess[0])
        lxv_all = np.array(correct_adressess[1])
    return fxv_all, lxv_all


def read_all_spectras(buff):
    end, npt_all, fxv_all, lxv_all = keyword_positions(buff)
    fxv_all, lxv_all = filter_unpaired(fxv_all, lxv_all)

    # Number of wavepoints
    npt = [unpack_from("<i", buff, adr)[0] for adr in npt_all]
    # "end_spc is vector of offsets where spectra start"
    end_spc = end[np.where(np.diff(end) > 4 * min(npt))]
    spc_param_list = {'npt': npt_all, 'fxv': fxv_all, 'lxv': lxv_all}

    # Filtering some corrupted series
    param_spc = filter_spc_params(end_spc, spc_param_list, npt_all)
    # Number of points in correct spectras
    npt_spc = [unpack_from("<i", buff, adr)[0] for adr in param_spc["npt"]]
    npt_spc = np.array(npt_spc)

    mask = npt_spc > 0
    for key in param_spc.keys():
        param_spc[key] = param_spc[key][mask]
    npt_spc = npt_spc[mask]

    def read_spec(x):
        return np.array(unpack_from("<" + str(x[1]) + "f", buff, x[0] - 4))

    def read_waves(x):
        return unpack_from("<2d", buff, x)[0]

    spc = map(read_spec, zip(param_spc['end'], npt_spc))
    fxv_spc = np.array(map(read_waves, param_spc["fxv"]))
    lxv_spc = map(lambda x: unpack_from("<2d", buff, x)[0], param_spc["lxv"])
    wavenumbers = generate_wavelengths(lxv_spc, fxv_spc, npt_spc)

    return fxv_spc, spc, wavenumbers


def generate_wavelengths(lxv_spc, fxv_spc, npt_spc):
    wavenumbers = []
    for lx, fx, npt1 in zip(lxv_spc, fxv_spc, npt_spc):
        ratio = (fx - lx) / (npt1 - 1)
        arr = np.flipud(np.arange(lx, fx + ratio, ratio))
        wavenumbers.append(arr)
    return wavenumbers


def get_meta_data(buff):
    # Getting source of instruments
    all_ins = tuple(find_all('INS', buff))
    inst = unpack_from("<3s", buff, all_ins[-1] + 8)[0]
    # Getting source of infrared <NIR/MIR>
    all_src = tuple(find_all('SRC', buff))
    src = unpack_from("<3s", buff, all_src[-1] + 5)[0]

    dat = buff.find('DAT') + 8
    scandate = unpack_from("10s", buff, dat)[0]

    snm = buff.find('SNM') + 8
    snm_lab_material = unpack_from("22s", buff, snm)[0]

    meta = {'ins': inst,
            'src': src,
            'date': scandate,
            'snm': snm_lab_material}
    return meta


def filter_spc_params(end_spc, spc_param_list, npt_all):
    def indexes_of_valid_series(arr):
        return list(arr).index(min(filter(lambda x: x > 0, arr)))
    new_end = []
    new_fxv = []
    new_lxv = []
    fxv_spc = spc_param_list['fxv']
    lxv_spc = spc_param_list['lxv']
    for npy in npt_all:
        end_diff = npy - end_spc
        lxv_diff = lxv_spc - npy
        fxv_diff = fxv_spc - npy
        lxv_tmp = indexes_of_valid_series(lxv_diff)
        fxv_tmp = indexes_of_valid_series(fxv_diff)
        end_tmp = indexes_of_valid_series(end_diff)
        new_end.append(end_spc[end_tmp])
        new_fxv.append(fxv_spc[fxv_tmp])
        new_lxv.append(lxv_spc[lxv_tmp])
    spc_param_list['end'] = np.array(new_end)
    spc_param_list['lxv'] = np.array(new_lxv)
    spc_param_list['fxv'] = np.array(new_fxv)

    return spc_param_list
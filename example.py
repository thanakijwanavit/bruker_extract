#!/usr/bin/env python
# coding: utf-8

# ## test object

# In[16]:


from bruker_load import Wave


# In[17]:


root="./sample_data"
wave_object=Wave(root)


# In[19]:


# list names of files
wave_object.list_names()


# In[20]:


## save file as csv
wave_object.to_csv('csv_test')


# In[21]:


#load csv file
wave_object.load_csv('./csv_test')


# In[22]:


# list names of files
wave_object.list_names()


# In[24]:


# plot chart of file (matplotlibb)
wave_object.plot('Fish Meal - RM_M359_12062019_MIX3_20190612_170936')


# In[ ]:





# In[ ]:





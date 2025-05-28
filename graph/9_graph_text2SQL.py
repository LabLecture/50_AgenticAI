#!/usr/bin/env python
# coding: utf-8

# In[5]:


from langchain_ollama import ChatOllama

# In[8]:


llm = ChatOllama(model="llama3.2:latest", emperature=0, base_url = "http://192.168.1.203:11434")
# llm = ChatOllama(model="mistral:latest", emperature=0, base_url = "http://61.108.166.16:11434")
llm.invoke('안녕하세요')

# In[ ]:




from sklearn.datasets import fetch_mldata
from tqdm import trange
import numpy as np
import random
import json
import os

random.seed(1)
np.random.seed(1)

# Setup directory for train/test data
train_path = './data/train/all_data_0_niid_0_keep_10_train_9.json'
test_path = './data/test/all_data_0_niid_0_keep_10_test_9.json'
dir_path = os.path.dirname(train_path)
if not os.path.exists(dir_path):
    os.makedirs(dir_path)
dir_path = os.path.dirname(test_path)
if not os.path.exists(dir_path):
    os.makedirs(dir_path)

# Get MNIST data, normalize, and divide by level
mnist = fetch_mldata('MNIST original', data_home='./data')
mu = np.mean(mnist.data.astype(np.float32), 0)
sigma = np.std(mnist.data.astype(np.float32), 0)
mnist.data = (mnist.data.astype(np.float32) - mu)/(sigma+0.001)
mnist_data = []
for i in trange(10):
    idx = mnist.target==i
    mnist_data.append(mnist.data[idx])

print("\nNumb samples of each label:\n", [len(v) for v in mnist_data])

###### CREATE USER DATA SPLIT #######
# Assign 100 samples to each user
X = [[] for _ in range(5)]
y = [[] for _ in range(5)]
idx = np.zeros(10, dtype=np.int64)
for user in range(5):
    for j in range(3):  # 3 labels for each users
        l = (2*user+j)%10
        print("L:",l)
        X[user] += mnist_data[l][idx[l]:idx[l]+10].tolist()
        y[user] += (l*np.ones(10)).tolist()
        idx[l] += 10

print("IDX1:", idx) # counting samples for each labels

# Assign remaining sample by power law
user = 0
props = np.random.lognormal(0, 2., (10,5,3)) # last 5 is 5 labels
# print("here:",props/np.sum(props,(1,2), keepdims=True))
props = np.array([[[len(v)-1000]] for v in mnist_data])*props/np.sum(props,(1,2), keepdims=True)
#idx = 1000*np.ones(10, dtype=np.int64)
# print("here2:",props)
for user in trange(5):
    for j in range(3):  # 4 labels for each users
        l = (2*user+j)%10
        num_samples = int(props[l,user,j])
        num_samples = min(num_samples,150)
        # print(num_samples)
        if idx[l] + num_samples < len(mnist_data[l]):
            X[user] += mnist_data[l][idx[l]:idx[l]+num_samples].tolist()
            y[user] += (l*np.ones(num_samples)).tolist()
            idx[l] += num_samples

print("IDX2:", idx) # counting samples for each labels

# Create data structure
train_data = {'users': [], 'user_data':{}, 'num_samples':[]}
test_data = {'users': [], 'user_data':{}, 'num_samples':[]}

# Setup 5 users
for i in trange(5, ncols=120):
    uname = 'f_{0:05d}'.format(i)
    
    combined = list(zip(X[i], y[i]))
    random.shuffle(combined)
    X[i][:], y[i][:] = zip(*combined)
    num_samples = len(X[i])
    train_len = int(0.9*num_samples)
    test_len = num_samples - train_len
    
    train_data['users'].append(uname) 
    train_data['user_data'][uname] = {'x': X[i][:train_len], 'y': y[i][:train_len]}
    train_data['num_samples'].append(train_len)
    test_data['users'].append(uname)
    test_data['user_data'][uname] = {'x': X[i][train_len:], 'y': y[i][train_len:]}
    test_data['num_samples'].append(test_len)

print("Num_samples:", train_data['num_samples'])
print("Total_samples:",sum(train_data['num_samples']))
    
with open(train_path,'w') as outfile:
    json.dump(train_data, outfile)
with open(test_path, 'w') as outfile:
    json.dump(test_data, outfile)

print("Finish Generating Samples")

import numpy as np
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import ExtraTreesClassifier
import matplotlib.pyplot as plt

np.set_printoptions(threshold=np.nan)

verbose = 1

filen = 'example_output'
outn = 'example_out'
data = []

# Load labeled training data
labdata = []
with open('../gen/training_lab_data', 'r') as f:	
    labdata = f.readlines()

if verbose == 1: print("--- loaded labeled data")

# Remove newlines and separate columns	
labdata = [x.strip('\n') for x in labdata] 
labdata = [x.split(" ") for x in labdata] 

n = len(labdata)
m = len(labdata[0])

xs = [x[: m - 1] for x in labdata]
ys = [x[m - 1] for x in labdata]

if verbose == 1: print("number of 1 (clickjacking): ", ys.count('1'))
if verbose == 1: print("number of 2 (malicious): ", ys.count('2'))
if verbose == 1: print("number of 3 (benign): ", ys.count('3'))

# Create validation set with train-test split 0.5
xs_train, xs_test, ys_train, ys_test = train_test_split(xs, ys, test_size = 0.5, random_state = 345) 

clf = ExtraTreesClassifier(n_estimators=50, max_features = m-1, max_depth=None, min_samples_split=1, \
	random_state=12, bootstrap=True) 

clf.fit(xs_train, ys_train)

prob = clf.predict_proba(xs_test)
pred = clf.predict(xs_test) 

# Analyze result
correct = 0
wrong = 0

falseneg = 0
falsepos = 0
# Correctly classified
crtclass = 0
trueclickj = 0
predclickj = 0

for i in range(0, len(xs_test)):
	result = pred[i]
	if verbose == 1: print(i, " ", ys_test[i], " pred: ", result, prob[i])
	
	if ys_test[i] == '1':
		trueclickj += 1
	if result == '1':
		predclickj += 1

	if ys_test[i] == '1' and result != '1':
		falseneg += 1
	if ys_test[i] != '1' and result == '1':
		falsepos += 1
	if ys_test[i] == '1' and result == '1':
		crtclass += 1

	if(ys_test[i] == result):
		correct = correct + 1
	else: wrong = wrong + 1

if verbose == 1: print("\n\ntotal: ", n)
if verbose == 1: print("correct: ", correct)
if verbose == 1: print("wrong: ", wrong, "\n")

accuracy = (correct * 100) / len(xs_test)
if verbose == 1: print("accuracy: ", accuracy, "\n\n")

if verbose == 1: print("falsepos: ", falsepos)
if verbose == 1: print("falseneg: ", falseneg)
if verbose == 1: print("crtclass: ", crtclass)

if verbose == 1: print("trueclickjickj: ", trueclickj, ", predclickjickj", predclickj)

importances = clf.feature_importances_
if verbose == 1: print("features as list:\n")
if verbose == 1: print(importances)

# Code from:
# http://scikit-learn.org/stable/auto_examples/ensemble/plot_forest_importances.html...
# ...example-ensemble-plot-forest-importances-py

# Print the feature ranking
indices = np.argsort(importances)[::-1]
if verbose == 1: print("\nFeature ranking:")
nf = m-1
for f in range(nf):
    if verbose == 1: print("%d. feature %d (%f)" % (f + 1, indices[f], importances[indices[f]]))

# Plot the feature importances
plt.figure()
plt.title("Feature importance")
plt.bar(range(nf), importances[indices], color="b", align="center")
plt.xticks(range(nf), indices)
plt.xlim([-1, nf])
plt.show()

# Train classifier on full training set
clf.fit(xs,ys)

# Load data
data = []
with open(''.join(('../gen/data_', filen)), 'r') as f:	
    data = f.readlines()
if verbose == 1: print("data file", filen, " loaded")

# Remove newlines and separate columns	
data = [x.strip('\n') for x in data] 
data = [x.split(" ") for x in data] 

n = len(data)
m = len(data[0])

xs = [x[: m - 1] for x in data]
ys = [x[m - 1] for x in data]

out = []
# Print predictions and probability
for i in range(0, len(ys)):
	out.append([i+1, "  pred:", pred[i], " prob:", prob[i]])

with open(''.join(('../out/', outn, ".txt")), 'w') as f:	
	for item in out:
		f.write("%s\n" % item)

if verbose == 1: print("output file", outn, " written")


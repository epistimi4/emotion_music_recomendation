import pandas as pd
import numpy as np
import sys
import argparse
from sklearn import preprocessing
from sklearn.metrics import accuracy_score
from sklearn import model_selection
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import confusion_matrix
import seaborn as sn
import matplotlib.pyplot as plt

DATASET_PATH = './Business Analysis/data/athina_playlist_metadata.xlsx'

def main(platform='spotify', users=[]):

    df = pd.read_excel(DATASET_PATH)
    df = preprocess_datasheet(df, users)
    if(platform == 'spotify'):
        Y_predicted, Y_real = spotify_generate_predictions(df)
        if(allUsersAskedFor(users)):
            plot_confusion_matrix(Y_real, Y_predicted, "heatmap_allUsers")
        elif(particularUsersAskedFor(users)):
            plot_confusion_matrix(Y_real, Y_predicted, "heatmap_users"+str(users))
    elif(platform == 'youtube'):
        print("Add youtube classifier")

def preprocess_datasheet(df, users=[]):
    df['user_id'] = df['user_id'].astype(int).astype(str)
    if (particularUsersAskedFor(users)):
        # ask for correlations of specific user
        df = df[df['user_id'].isin(users)]
    df = df.dropna(axis=0)

    loudness = df.take([3], axis=1).values
    df['loudness'] = preprocessing.MinMaxScaler().fit_transform(loudness)
    return df

def spotify_generate_predictions(df):
    X = df.take([1,5,6,9,10,12,18,21], axis=1)  # predictors
    X = X.apply(pd.to_numeric)
    X = X.iloc[1:]

    df = unify_classes(df)
    df['Class'] = df['mood'] + "_at_" + df['location'] + "_while_" + df['activity_unified']
    Y = df['Class']  # predicted_class
    Y = Y.iloc[1:]

    classes = np.unique(df['Class'].values)
    print("We have {} unique classes: {}".format(len(classes), classes))

    seed = 7
    num_trees = 30
    kfold = model_selection.KFold(n_splits=10, random_state=seed)
    model = AdaBoostClassifier(n_estimators=num_trees, random_state=seed)
    predictions = model_selection.cross_val_predict(model, X, Y.values.ravel(), cv=kfold)

    accuracy = accuracy_score(Y.values.ravel(), predictions)
    print("accuracy = ", accuracy)

    return predictions, Y


def unify_classes(df):
    df['mood'] = df['mood'].replace({'angry': 'unhappy', 'sad': 'unhappy', 'nervous': 'unhappy'})
    df['mood'] = df['mood'].replace({'bored': 'annoyed', 'sleepy': 'annoyed'})
    df['mood'] = df['mood'].replace({'calm': 'relaxed', 'relaxed': 'relaxed', 'peaceful': 'relaxed'})
    df['mood'] = df['mood'].replace({'excited': 'happy', 'happy': 'happy', 'pleased': 'happy'})
    df['activity_unified'] = df['activity']
    df['activity_unified'] = df['activity_unified'].replace({'commuting': 'other'})
    return df

def allUsersAskedFor(users=['0']):
    return len(users) > 0 and users[0] == '0'

def particularUsersAskedFor(users=['0']):
    return len(users) > 0 and users[0] != '0'

def plot_confusion_matrix(Y, predictions,name):
    cf_matrix = confusion_matrix(predictions, Y.values.ravel())
    classes = np.unique(Y.values)
    fig = plt.figure(figsize=(25, 25)) #figsize=(20, 20)
    mood_matx = sn.heatmap(cf_matrix / np.sum(cf_matrix), annot=True, xticklabels=classes, yticklabels=classes,
                           fmt='.2%', cmap='Reds')
    mood_matx.set_xticklabels(mood_matx.get_xticklabels(), rotation=90)
    plt.xlabel('Predicted Class')
    plt.ylabel('Real Class')
    fig.savefig("correlations/figures/"+name+".png")

# Predict regarding all users: Classifier.py -p spotify
# Predict regarding user 1: Classifier.py -p spotify -u 1
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', '-p', help="spotify or youtube", type=str)
    parser.add_argument('--users', '-u', help="id(s) of users separated by commas", type=int, default=0)

    args = parser.parse_args(sys.argv[1:])
    platform = args.platform #spotify or youtube
    users = str(args.users).split(',') #for all users the empty parameter is translated to ['0']
    main(platform, users)

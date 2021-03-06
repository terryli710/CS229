import collections

import numpy as np

import util
import svm


def get_words(message):
    """Get the normalized list of words from a message string.

    This function should split a message into words, normalize them, and return
    the resulting list. For splitting, you should split on spaces. For normalization,
    you should convert everything to lowercase.

    Args:
        message: A string containing an SMS message

    Returns:
       The list of normalized words from the message.
    """

    # *** START CODE HERE ***
    lower_message = message.lower()
    word_list = lower_message.split()
    return word_list
    # *** END CODE HERE ***


def create_dictionary(messages):
    """Create a dictionary mapping words to integer indices.

    This function should create a dictionary of word to indices using the provided
    training messages. Use get_words to process each message.

    Rare words are often not useful for modeling. Please only add words to the dictionary
    if they occur in at least five messages.

    Args:
        messages: A list of strings containing SMS messages

    Returns:
        A python dict mapping words to integers.
    """

    # *** START CODE HERE ***
    word_count = {}
    for msg in messages:
        word_set = set(get_words(msg))
        # words are unique now
        for word in word_set:
            # If new word, set count = 1
            if word not in word_count:
                word_count[word] = 1
            # If old word, count += 1
            else:
                word_count[word] += 1
    # for each word in count, if at least 5, add to dictionary
    dictionary = {}
    index = 0
    for word in word_count:
        if word_count[word] >= 5:
            dictionary[word] = index
            index += 1
    return dictionary
    # *** END CODE HERE ***


def transform_text(messages, word_dictionary):
    """Transform a list of text messages into a numpy array for further processing.

    This function should create a numpy array that contains the number of times each word
    of the vocabulary appears in each message. 
    Each row in the resulting array should correspond to each message 
    and each column should correspond to a word of the vocabulary.

    Use the provided word dictionary to map words to column indices. Ignore words that
    are not present in the dictionary. Use get_words to get the words for a message.

    Args:
        messages: A list of strings where each string is an SMS message.
        word_dictionary: A python dict mapping words to integers.

    Returns:
        A numpy array marking the words present in each message.
        Where the component (i,j) is the number of occurrences of the
        j-th vocabulary word in the i-th message.
    """
    # *** START CODE HERE ***
    text_matrix = np.zeros((len(messages), len(word_dictionary)))
    for i in range(len(messages)):
        word_list = get_words(messages[i])
        for word in word_list:
            if word in word_dictionary:
                j = word_dictionary[word]
                text_matrix[i,j] += 1
    return text_matrix
    # *** END CODE HERE ***


def fit_naive_bayes_model(matrix, labels):
    """Fit a naive bayes model.

    This function should fit a Naive Bayes model given a training matrix and labels.

    The function should return the state of that model.

    Feel free to use whatever datatype you wish for the state of the model.

    Args:
        matrix: A numpy array containing word counts for the training data
        labels: The binary (0 or 1) labels for that training data

    Returns: The trained model
    """

    # *** START CODE HERE ***
    class naiveBayes():
        def __init__(self):
            self.phi_pos = None
            self.phi_neg = None
            self.prob_pos = None
        def fit(self, matrix, labels):
            exist_matrix = (matrix>0).astype('int')
            # Calculate phi_j, using Laplace smoothing
            spam_count = exist_matrix * labels.reshape(labels.shape[0], 1)
            self.phi_pos = (np.sum(spam_count, axis=0, keepdims=True) + 1) /(np.sum(labels) + 2)
            nonspam_count = exist_matrix * (labels==0).reshape((labels==0).shape[0], 1)
            self.phi_neg = (np.sum(nonspam_count, axis=0, keepdims=True) + 1) /(np.sum(labels==0) + 2)
            # Calculate probability of positive as a whole
            self.prob_pos = np.mean(labels)
    naiveBayesModel = naiveBayes()
    naiveBayesModel.fit(matrix, labels)
    return naiveBayesModel
    # *** END CODE HERE ***


def predict_from_naive_bayes_model(model, matrix):
    """Use a Naive Bayes model to compute predictions for a target matrix.

    This function should be able to predict on the models that fit_naive_bayes_model
    outputs.

    Args:
        model: A trained model from fit_naive_bayes_model
        matrix: A numpy array containing word counts

    Returns: A numpy array containing the predictions from the model
    """
    # *** START CODE HERE ***
    # For more stable output, use log instead of prod
    # score = sum(log(p(x_i|y))) + p(y)
    # where p(x_i|y) = model.phi[i]
    pos_score = np.sum(np.log(model.phi_pos) * matrix, axis=1, keepdims=True) + np.log(model.prob_pos)
    neg_score = np.sum(np.log(model.phi_neg) * matrix, axis=1, keepdims=True) + np.log(1-model.prob_pos)
    predicts = np.zeros((matrix.shape[0],1))
    predicts[pos_score>neg_score] = 1
    return predicts
    # *** END CODE HERE ***


def get_top_five_naive_bayes_words(model, dictionary):
    """Compute the top five words that are most indicative of the spam (i.e positive) class.

    Ues the metric given in part-c as a measure of how indicative a word is.
    Return the words in sorted form, with the most indicative word first.

    Args:
        model: The Naive Bayes model returned from fit_naive_bayes_model
        dictionary: A mapping of word to integer ids

    Returns: A list of the top five most indicative words in sorted order with the most indicative first
    """
    # *** START CODE HERE ***
    indicative = (model.phi_pos / model.phi_neg).reshape(model.phi_pos.shape[1])
    top_five_index = indicative.argsort()[-5:][::-1]
    # Find top five words by finding the keys from values in dictionary
    top_five_words = [None] * 5
    for key, value in dictionary.items():
        if value in top_five_index:
            rank = np.where(top_five_index == value)[0][0]
            top_five_words[rank] = key
    return top_five_words
    # *** END CODE HERE ***


def compute_best_svm_radius(train_matrix, train_labels, val_matrix, val_labels, radius_to_consider):
    """Compute the optimal SVM radius using the provided training and evaluation datasets.

    You should only consider radius values within the radius_to_consider list.
    You should use accuracy as a metric for comparing the different radius values.

    Args:
        train_matrix: The word counts for the training data
        train_labels: The spam or not spam labels for the training data
        val_matrix: The word counts for the validation data
        val_labels: The spam or not spam labels for the validation data
        radius_to_consider: The radius values to consider

    Returns:
        The best radius which maximizes SVM accuracy.
    """
    # *** START CODE HERE ***
    accuracy_list = [None] * len(radius_to_consider)
    for i in range(len(radius_to_consider)):
        predicts = svm.train_and_predict_svm(train_matrix, train_labels, val_matrix, radius_to_consider[i])
        accuracy_list[i] = np.mean(predicts==val_labels)
    best_index = accuracy_list.index(max(accuracy_list))
    return radius_to_consider[best_index]
    # *** END CODE HERE ***


def main():
    train_messages, train_labels = util.load_spam_dataset('spam_train.tsv')
    val_messages, val_labels = util.load_spam_dataset('spam_val.tsv')
    test_messages, test_labels = util.load_spam_dataset('spam_test.tsv')

    dictionary = create_dictionary(train_messages)

    print('Size of dictionary: ', len(dictionary))

    util.write_json('spam_dictionary', dictionary)

    train_matrix = transform_text(train_messages, dictionary)

    np.savetxt('spam_sample_train_matrix', train_matrix[:100,:])

    val_matrix = transform_text(val_messages, dictionary)
    test_matrix = transform_text(test_messages, dictionary)

    naive_bayes_model = fit_naive_bayes_model(train_matrix, train_labels)

    naive_bayes_predictions = predict_from_naive_bayes_model(naive_bayes_model, test_matrix)

    np.savetxt('spam_naive_bayes_predictions', naive_bayes_predictions)

    naive_bayes_accuracy = np.mean(naive_bayes_predictions == test_labels)

    print('Naive Bayes had an accuracy of {} on the testing set'.format(naive_bayes_accuracy))

    top_5_words = get_top_five_naive_bayes_words(naive_bayes_model, dictionary)

    print('The top 5 indicative words for Naive Bayes are: ', top_5_words)

    util.write_json('spam_top_indicative_words', top_5_words)

    optimal_radius = compute_best_svm_radius(train_matrix, train_labels, val_matrix, val_labels, [0.01, 0.1, 1, 10])

    util.write_json('spam_optimal_radius', optimal_radius)

    print('The optimal SVM radius was {}'.format(optimal_radius))

    svm_predictions = svm.train_and_predict_svm(train_matrix, train_labels, test_matrix, optimal_radius)

    svm_accuracy = np.mean(svm_predictions == test_labels)

    print('The SVM model had an accuracy of {} on the testing set'.format(svm_accuracy, optimal_radius))


if __name__ == "__main__":
    main()

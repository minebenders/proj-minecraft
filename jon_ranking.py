from data import *

def main():

    itr = text1 # Choose text1, text2, or text3
    queries = SentenceQ # Choose ConvictionTrialQ, ConvictionAppealQ, TraffickingQ, KnowledgeQ, PossessionQ, CourierQ, SentenceQ
    scorethreshold = 2 # If there are too many low scores, change the threshold to a higher number

    output = rule1(itr, queries, scorethreshold)

    print(output)
    for para in output:
        print(para, itr[para])

def rule1(itr, queries, scorethreshold):
    """
    Rule 1 gives an equal weightage to each keyword
    """
    output = dict()
    for para in itr:
        score = 0
        for word in queries:
            if word in itr[para]:
                score += 1 
        if score > scorethreshold: 
            output[para] = score

    output = {k: v for k, v in sorted(output.items(), key=lambda x: x[1], reverse=True)}
    return output

main()
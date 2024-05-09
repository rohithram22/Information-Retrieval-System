import argparse
import math
import matplotlib.pyplot as plt

def read_qrel(qrel_file):
    qrel = {}
    with open(qrel_file, 'r') as f:
        for line in f:
            topic, _, doc_id, rel = line.strip().split()
            if topic not in qrel:
                qrel[topic] = {}
            qrel[topic][doc_id] = int(rel)
    return qrel

def read_trec(trec_file):
    trec = {}
    with open(trec_file, 'r') as f:
        for line in f:
            topic, _, doc_id, _, score, _ = line.strip().split()
            if topic not in trec:
                trec[topic] = {}
            trec[topic][doc_id] = float(score)
    return trec

def evaluate(qrel, trec, print_all_queries):
    metrics = {'map': 0.0, 'ndcg': 0.0, 'r_prec': 0.0}
    cutoffs = [5, 10, 15, 20, 30, 100, 200, 500, 1000]
    for cutoff in cutoffs:
        metrics[f'p_{cutoff}'] = 0.0
        metrics[f'r_{cutoff}'] = 0.0
        metrics[f'f1_{cutoff}'] = 0.0
    
    num_topics = 0
    tot_num_ret = 0
    tot_num_rel = 0
    tot_num_rel_ret = 0
    
    for topic in sorted(trec.keys()):
        if topic not in qrel:
            continue
        
        num_topics += 1
        retrieved_docs = sorted(trec[topic].items(), key=lambda x: x[1], reverse=True)
        num_rel = sum(qrel[topic].values())
        num_ret = len(retrieved_docs)
        
        # Precision, Recall, F1 at cutoffs
        precision = []
        recall = []
        for cutoff in cutoffs:
            cutoff_docs = retrieved_docs[:cutoff]
            num_rel_ret = sum(qrel[topic].get(doc_id, 0) for doc_id, _ in cutoff_docs)
            metrics[f'p_{cutoff}'] += num_rel_ret / cutoff
            metrics[f'r_{cutoff}'] += num_rel_ret / num_rel if num_rel > 0 else 0.0
            metrics[f'f1_{cutoff}'] += 2 * metrics[f'p_{cutoff}'] * metrics[f'r_{cutoff}'] / (metrics[f'p_{cutoff}'] + metrics[f'r_{cutoff}']) if metrics[f'p_{cutoff}'] + metrics[f'r_{cutoff}'] > 0 else 0.0
            precision.append(num_rel_ret / cutoff)
            recall.append(num_rel_ret / num_rel if num_rel > 0 else 0.0)
        
        # R-Precision
        r_prec_cutoff = num_rel
        r_prec_docs = retrieved_docs[:r_prec_cutoff]
        num_rel_ret = sum(qrel[topic].get(doc_id, 0) for doc_id, _ in r_prec_docs)
        metrics['r_prec'] += num_rel_ret / num_rel if num_rel > 0 else 0.0
        
        # Average Precision
        ap = 0.0
        num_rel_ret = 0
        for i, (doc_id, _) in enumerate(retrieved_docs):
            if qrel[topic].get(doc_id, 0) > 0:
                num_rel_ret += 1
                ap += num_rel_ret / (i + 1)
        ap /= num_rel if num_rel > 0 else 0.0
        metrics['map'] += ap
        
        # nDCG
        idcg = sum(1.0 / math.log2(i + 2) for i in range(num_rel))
        dcg = 0.0
        for i, (doc_id, _) in enumerate(retrieved_docs):
            rel = qrel[topic].get(doc_id, 0)
            if rel > 0:
                dcg += (2 ** rel - 1) / math.log2(i + 2)
        ndcg = dcg / idcg if idcg > 0 else 0.0
        metrics['ndcg'] += ndcg
        
        tot_num_ret += num_ret
        tot_num_rel += num_rel
        tot_num_rel_ret += num_rel_ret
        
        if print_all_queries:
            print(f"\nQueryid (Num):    {topic}")
            print(f"R-Precision:      {metrics['r_prec'] / num_topics:.4f}")
            print(f"Average Precision: {ap:.4f}")
            print(f"nDCG:             {ndcg:.4f}")
            for cutoff in cutoffs:
                print(f"Precision@{cutoff}:     {metrics[f'p_{cutoff}'] / num_topics:.4f}")
                print(f"Recall@{cutoff}:        {metrics[f'r_{cutoff}'] / num_topics:.4f}")
                print(f"F1@{cutoff}:            {metrics[f'f1_{cutoff}'] / num_topics:.4f}")
            
            # Plot precision-recall curve
            plt.figure(figsize=(8, 6))
            plt.plot(recall, precision, marker='o', linestyle='-', linewidth=2)
            plt.xlabel('Recall')
            plt.ylabel('Precision')
            plt.title(f'Precision-Recall Curve for Query {topic}')
            plt.grid(True)
            plt.savefig(f'precision_recall_query_{topic}.png')
    
    # Average metrics over all queries
    for metric in metrics:
        metrics[metric] /= num_topics
    
    print(f"\nQueryid (Num):    {num_topics}")
    print(f"R-Precision:      {metrics['r_prec']:.4f}")
    print(f"Average Precision: {metrics['map']:.4f}")
    print(f"nDCG:             {metrics['ndcg']:.4f}")
    for cutoff in cutoffs:
        print(f"Precision@{cutoff}:     {metrics[f'p_{cutoff}']:.4f}")
        print(f"Recall@{cutoff}:        {metrics[f'r_{cutoff}']:.4f}")
        print(f"F1@{cutoff}:            {metrics[f'f1_{cutoff}']:.4f}")
    
def main():
    parser = argparse.ArgumentParser(description='Evaluate TREC-style runs')
    parser.add_argument('qrel_file', help='QREL file')
    parser.add_argument('trec_file', help='TREC run file')
    parser.add_argument('-q', '--print_all_queries', action='store_true', help='Print metrics for each query')
    args = parser.parse_args()
    
    qrel = read_qrel(args.qrel_file)
    trec = read_trec(args.trec_file)
    evaluate(qrel, trec, True)

if __name__ == '__main__':
    main()
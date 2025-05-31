#!/bin/bash

# Performance Testing Script for Information Retrieval System
# This script runs comprehensive tests and collects statistics

# Configuration
CORPUS_FILE="corpus.jsonl"
MINI_CORPUS_FILE="mini-corpus.jsonl"
INDEX_DIR="indexes"
QUERIES_FILE="queries.txt"
RESULTS_FILE="performance_results.txt"
MEMORY_LIMIT=1024

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Function to check if file exists
check_file() {
    if [ ! -f "$1" ]; then
        print_error "File $1 not found!"
        return 1
    fi
    return 0
}

# Create results file
create_results_file() {
    cat > "$RESULTS_FILE" << EOF
# Information Retrieval System Performance Results
# Generated on: $(date)
# System: $(uname -a)
# Python Version: $(python3 --version)

================================================================================
SYSTEM CONFIGURATION
================================================================================
Memory Limit: ${MEMORY_LIMIT} MB
Corpus File: ${CORPUS_FILE}
Index Directory: ${INDEX_DIR}
CPU Cores: $(nproc)
Available Memory: $(free -h | grep '^Mem:' | awk '{print $2}')

EOF
}

# Function to get corpus statistics
get_corpus_stats() {
    print_status "Analyzing corpus statistics..."
    
    echo "================================================================================
CORPUS ANALYSIS
================================================================================" >> "$RESULTS_FILE"
    
    if check_file "$CORPUS_FILE"; then
        local doc_count=$(wc -l < "$CORPUS_FILE")
        local file_size=$(ls -lh "$CORPUS_FILE" | awk '{print $5}')
        local file_size_bytes=$(stat -f%z "$CORPUS_FILE" 2>/dev/null || stat -c%s "$CORPUS_FILE" 2>/dev/null)
        
        echo "Total Documents: $doc_count" >> "$RESULTS_FILE"
        echo "Corpus File Size: $file_size" >> "$RESULTS_FILE"
        echo "Corpus File Size (bytes): $file_size_bytes" >> "$RESULTS_FILE"
        
        # Sample first few documents to get structure info
        echo "
Sample Document Structure:" >> "$RESULTS_FILE"
        head -n 3 "$CORPUS_FILE" | python3 -m json.tool | head -n 20 >> "$RESULTS_FILE"
        echo "..." >> "$RESULTS_FILE"
        
        print_status "Corpus has $doc_count documents ($file_size)"
    else
        print_warning "Corpus file not found. Using mini-corpus if available."
        if check_file "$MINI_CORPUS_FILE"; then
            CORPUS_FILE="$MINI_CORPUS_FILE"
            local doc_count=$(wc -l < "$CORPUS_FILE")
            echo "Using Mini-Corpus: $doc_count documents" >> "$RESULTS_FILE"
        fi
    fi
    
    echo "" >> "$RESULTS_FILE"
}

# Function to run indexer and collect statistics
run_indexer() {
    print_status "Running indexer with memory limit ${MEMORY_LIMIT}MB..."
    
    echo "================================================================================
INDEXING PERFORMANCE
================================================================================" >> "$RESULTS_FILE"
    
    # Clean previous indexes
    if [ -d "$INDEX_DIR" ]; then
        rm -rf "$INDEX_DIR"
    fi
    
    # Run indexer and capture all output
    local start_time=$(date +%s)
    
    echo "Indexing Started: $(date)" >> "$RESULTS_FILE"
    echo "Command: python3 indexer.py -m $MEMORY_LIMIT -c $CORPUS_FILE -i $INDEX_DIR" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    # Run indexer with timing and capture both stdout and stderr
    {
        time python3 indexer.py -m "$MEMORY_LIMIT" -c "$CORPUS_FILE" -i "$INDEX_DIR" 2>&1
    } > indexer_output.tmp 2>&1
    
    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))
    
    echo "Indexing Completed: $(date)" >> "$RESULTS_FILE"
    echo "Wall Clock Time: ${total_time} seconds" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    # Extract JSON statistics from indexer output
    echo "Indexer Statistics:" >> "$RESULTS_FILE"
    grep '{' indexer_output.tmp | tail -n 1 >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    # Capture console output (partial index flushes, etc.)
    echo "Indexer Console Output:" >> "$RESULTS_FILE"
    cat indexer_output.tmp >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    # Clean up temporary file
    rm -f indexer_output.tmp
    
    print_status "Indexing completed in ${total_time} seconds"
}

# Function to analyze index files
analyze_index() {
    print_status "Analyzing generated index files..."
    
    echo "================================================================================
INDEX FILE ANALYSIS
================================================================================" >> "$RESULTS_FILE"
    
    if [ -d "$INDEX_DIR" ]; then
        echo "Index Directory Contents:" >> "$RESULTS_FILE"
        ls -lh "$INDEX_DIR" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        
        echo "Total Index Size:" >> "$RESULTS_FILE"
        du -sh "$INDEX_DIR" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        
        # Analyze individual files
        for file in "$INDEX_DIR"/*; do
            if [ -f "$file" ]; then
                local basename=$(basename "$file")
                local size=$(ls -lh "$file" | awk '{print $5}')
                local lines=$(wc -l < "$file" 2>/dev/null || echo "N/A")
                echo "$basename: $size ($lines lines)" >> "$RESULTS_FILE"
            fi
        done
        echo "" >> "$RESULTS_FILE"
        
        # Analyze term lexicon if it exists
        if [ -f "$INDEX_DIR/term_lexicon.json" ]; then
            echo "Term Lexicon Analysis:" >> "$RESULTS_FILE"
            python3 -c "
import json
with open('$INDEX_DIR/term_lexicon.json') as f:
    lexicon = json.load(f)
    print(f'Total unique terms: {len(lexicon)}')
    dfs = [entry['df'] for entry in lexicon.values()]
    print(f'Min document frequency: {min(dfs)}')
    print(f'Max document frequency: {max(dfs)}')
    print(f'Average document frequency: {sum(dfs)/len(dfs):.2f}')
    print(f'Terms with DF=1: {sum(1 for df in dfs if df == 1)}')
    print(f'Terms with DF>100: {sum(1 for df in dfs if df > 100)}')
" >> "$RESULTS_FILE"
            echo "" >> "$RESULTS_FILE"
        fi
    else
        echo "Index directory not found!" >> "$RESULTS_FILE"
        print_error "Index directory not found!"
    fi
}

# Function to run query processor and collect statistics
run_queries() {
    print_status "Running query processor tests..."
    
    echo "================================================================================
QUERY PROCESSING PERFORMANCE
================================================================================" >> "$RESULTS_FILE"
    
    if [ ! -d "$INDEX_DIR" ]; then
        print_error "Index directory not found. Run indexer first."
        return 1
    fi
    
    local query_count=$(wc -l < "$QUERIES_FILE")
    echo "Test Queries File: $QUERIES_FILE" >> "$RESULTS_FILE"
    echo "Number of Test Queries: $query_count" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    # Test both ranking functions
    for ranker in "TFIDF" "BM25"; do
        echo "Testing $ranker Ranking:" >> "$RESULTS_FILE"
        echo "Command: python3 processor.py -i $INDEX_DIR -q $QUERIES_FILE -r $ranker" >> "$RESULTS_FILE"
        
        local start_time=$(date +%s.%N)
        
        # Run query processor and capture output
        python3 processor.py -i "$INDEX_DIR" -q "$QUERIES_FILE" -r "$ranker" > "${ranker}_results.json" 2>&1
        local exit_code=$?
        
        local end_time=$(date +%s.%N)
        local elapsed=$(echo "$end_time - $start_time" | bc -l)
        local avg_time=$(echo "scale=4; $elapsed / $query_count" | bc -l)
        
        echo "Exit Code: $exit_code" >> "$RESULTS_FILE"
        echo "Total Time: ${elapsed} seconds" >> "$RESULTS_FILE"
        echo "Average Time per Query: ${avg_time} seconds" >> "$RESULTS_FILE"
        
        if [ $exit_code -eq 0 ]; then
            # Analyze results
            echo "Results Analysis:" >> "$RESULTS_FILE"
            python3 -c "
import json
import sys
results = []
try:
    with open('${ranker}_results.json') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    
    total_results = sum(len(r['Results']) for r in results)
    non_empty = sum(1 for r in results if r['Results'])
    
    print(f'Queries processed: {len(results)}')
    print(f'Queries with results: {non_empty}')
    print(f'Total results returned: {total_results}')
    print(f'Average results per query: {total_results/len(results):.2f}')
    
    # Score statistics
    all_scores = [result['Score'] for r in results for result in r['Results']]
    if all_scores:
        print(f'Score range: {min(all_scores):.4f} - {max(all_scores):.4f}')
        print(f'Average score: {sum(all_scores)/len(all_scores):.4f}')
    
except Exception as e:
    print(f'Error analyzing results: {e}')
" >> "$RESULTS_FILE"
        else
            echo "Query processing failed!" >> "$RESULTS_FILE"
        fi
        echo "" >> "$RESULTS_FILE"
        
        print_status "$ranker queries completed in ${elapsed}s (avg: ${avg_time}s per query)"
    done
    
    # Compare ranking functions if both succeeded
    echo "Ranking Function Comparison:" >> "$RESULTS_FILE"
    python3 -c "
import json
try:
    tfidf_results = []
    bm25_results = []
    
    with open('TFIDF_results.json') as f:
        for line in f:
            if line.strip():
                tfidf_results.append(json.loads(line))
    
    with open('BM25_results.json') as f:
        for line in f:
            if line.strip():
                bm25_results.append(json.loads(line))
    
    print(f'TFIDF queries: {len(tfidf_results)}')
    print(f'BM25 queries: {len(bm25_results)}')
    
    # Compare score distributions
    tfidf_scores = [r['Score'] for res in tfidf_results for r in res['Results']]
    bm25_scores = [r['Score'] for res in bm25_results for r in res['Results']]
    
    if tfidf_scores and bm25_scores:
        print(f'TFIDF avg score: {sum(tfidf_scores)/len(tfidf_scores):.4f}')
        print(f'BM25 avg score: {sum(bm25_scores)/len(bm25_scores):.4f}')
        
        # Overlap analysis for first query
        if tfidf_results and bm25_results:
            tfidf_docs = set(r['ID'] for r in tfidf_results[0]['Results'])
            bm25_docs = set(r['ID'] for r in bm25_results[0]['Results'])
            overlap = len(tfidf_docs & bm25_docs)
            print(f'Top-10 overlap (first query): {overlap}/10 documents')
    
except Exception as e:
    print(f'Error comparing rankings: {e}')
" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
}

# Function to run system monitoring
monitor_system() {
    print_status "Collecting system information..."
    
    echo "================================================================================
SYSTEM MONITORING
================================================================================" >> "$RESULTS_FILE"
    
    echo "Memory Usage:" >> "$RESULTS_FILE"
    free -h >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    echo "Disk Usage:" >> "$RESULTS_FILE"
    df -h . >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    echo "CPU Information:" >> "$RESULTS_FILE"
    lscpu | grep -E '^CPU\(s\)|^Model name|^CPU MHz' >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
}

# Function to generate summary
generate_summary() {
    print_status "Generating performance summary..."
    
    echo "================================================================================
PERFORMANCE SUMMARY
================================================================================" >> "$RESULTS_FILE"
    
    python3 -c "
import json
import os

print('=== KEY METRICS ===')

# Extract indexer stats
try:
    with open('indexer_output.tmp', 'r') as f:
        content = f.read()
        # Find JSON line
        for line in content.split('\n'):
            if line.strip().startswith('{') and 'Index Size' in line:
                stats = json.loads(line)
                print(f'Index Size: {stats[\"Index Size\"]} MB')
                print(f'Indexing Time: {stats[\"Elapsed Time\"]} seconds')
                print(f'Unique Terms: {stats[\"Number of Lists\"]}')
                print(f'Avg Posting List Size: {stats[\"Average List Size\"]}')
                break
except:
    print('Indexer statistics not available')

# Check if index files exist
if os.path.exists('$INDEX_DIR'):
    print(f'Index directory size: ', end='')
    os.system('du -sh $INDEX_DIR | cut -f1')

print('')
print('Test completed successfully!')
print('Results saved to: $RESULTS_FILE')
" >> "$RESULTS_FILE"
}

# Main execution
main() {
    print_status "Starting Information Retrieval System Performance Testing"
    print_info "Results will be saved to: $RESULTS_FILE"
    
    # Create results file
    create_results_file
    
    # Check prerequisites
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found!"
        exit 1
    fi
    
    if ! check_file "indexer.py" || ! check_file "processor.py"; then
        print_error "indexer.py or processor.py not found in current directory!"
        exit 1
    fi
    
    # Run all tests
    monitor_system
    get_corpus_stats
    run_indexer
    analyze_index
    run_queries
    generate_summary
    
    print_status "Performance testing completed!"
    print_info "Results saved to: $RESULTS_FILE"
    print_info "Query results saved to: TFIDF_results.json and BM25_results.json"
    
    # Show summary
    echo ""
    echo "=== QUICK SUMMARY ==="
    tail -n 20 "$RESULTS_FILE"
}

# Run main function
main "$@"

import os
import pandas as pd
import numpy as np
import itertools
import re

from Bio import SeqIO


def get_special_characters(my_string):
	"""Returns all unique characters of an input string that aren't alphanumeric characters.

	Params
    ------
    my_string: str; any input string

    Returns
    -------
    letters_ls: list of string; list of all unique special characters.
	"""
    letters_ls = list(set(list(re.sub(r'[a-zA-Z0-9]', '', my_string))))
    return letters_ls


def check_df_headers(df, colname="header"):
	"""Check dataframe headers for special characters. 
	Note: only tells you what characters exist; not what the offending headers are. 

	Params
    ------
    df: input pandas dataframe
    colname: column name of df to scan for special characters.

    Returns
    -------
    charset_ls: list of string; list of all unique special characters.
	"""
	charset_ls = []
	for index, row in df.iterrows():
	    charset_ls.append(get_special_char(str(row[colname])))

	charset_ls = set([x for y in charset_ls for x in y])

	return charset_ls


def choose_string_sections(seq, coords_ls):
    """Given a sequence seq, extract the relevant portions using the coords given in coords_ls. 
    Hasn't been used for quite awhile, though.

    Params
    ------
    seq: str. A nuc sequence.
    coords_ls: list of lists, where each element list is a set of coordinates.

    Returns
    -------
    sections_ls: list of string.

    >> seq = "ACGTACGTACGT"
    >> coords_ls = [[0, 4], [1, 5], [5, 8]]
    >> choose_gene_sections(seq, coords_ls)
    ['ACGT', 'CGTA', 'CGT']
    """
    section_ls = []
    for coord in coords_ls:
        s, t = coord
        section_ls.append(seq[s:t])
    return section_ls


def string_similarity(a, b, method='hamming', score_matrix=1, verbose=True):
    """Computes string similarity for two strings, a and b, using some
    similarity method.

    Params
    ------
    a, b: strings
    method: Various methods for computing string similarity. Available so far:
    Hamming distance
    score_matrix: unused param, to be used for edit distance implementations.
    verbose: Tells you what's happening when True.

    Return
    ------
    score: int; similarity score, computed using the specified input method.
    """
    if method == 'hamming':
        if len(a) != len(b):
            if verbose:
                print("Note: len(a)!=len(b)")
            x = min([a, b], key=len)
            y = max([a, b], key=len)
        else:
            x = a; y = b
        score = 0
        for i in range(len(x)):
            if x[i] != y[i]:
                score +=1
    return score


def self_similarity_matrix(str_ls):
    """Returns an upper triangular similarity matrix of all pairwise distances
    between possible pairs in str_ls. Only hamming distance implemented so far,
    so we require all elements in str_ls to be of the same length.
    """
    all_pairs = list(itertools.combinations((str_ls), 2))
    hamming_ls = []
    n_seq = len(str_ls)
    for pair in all_pairs:
        x, y = pair
        hamming_d = string_similarity(x, y)
        hamming_ls.append(hamming_d)

    # Construct heatmap data
    hm_data = np.zeros((n_seq, n_seq))
    idx = 0
    for i in range(n_seq):
        for j in range(i+1, n_seq):
            hm_data[i][j] = hamming_ls[idx]
            idx += 1

    return hm_data


def similarity_matrix(ls1, ls2, verbose=True):
    """Returns a similarity matrix of the hamming distance between all pairs
    ls1[i] and ls2[j].

    Params
    ------
    ls1, ls2: list of strings.
    verbose: Boolean. Not used within this function; gets passed to
    string_similarity().

    Returns
    -------
    M: array of int; shape(len(ls1), len(ls2))
    """
    n1 = len(ls1); n2 = len(ls2)
    M = np.zeros((n1, n2))
    for i in range(n1):
        for j in range(n2):
            M[i][j] = string_similarity(ls1[i], ls2[j], verbose=verbose)
    return M


def NW_mxs(a, b, method='bool', m=1, x=-1, s=-1):
    """Take 2 strings, a and b, of lengths n1 and n2, and compute NW edit
    distance between them
    Compute a matrix S of shape n1+1 by n2+1, and recursively fill it.

    Params
    ------
    a, b: input strings
    m: int, match score
    x: int, mismatch score
    s: int, 'gap' score

    Returns
    -------
    H: edit distance matrix
    tr: traceback matrix
    """
    n1 = len(a)
    n2 = len(b)
    H = np.zeros([n1+1,n2+1])
    dt = np.dtype("i4, i4")
    tb = np.zeros([n1+1,n2+1], dtype=dt)

    for i in range(1,n1+1):
        H[i][0] = i*s
    for j in range(1,n2+1):
        H[0][j] = j*s

    if method == 'bool':
        for i in range(1, n1+1):
            for j in range(1, n2+1):
                H[i][j] = max(H[i-1][j] + s,
                              H[i][j-1] + s,
                              H[i-1][j-1] + x*_bool_match(a[i-1], b[j-1]))
                #Fill in a traceback matrix
                #In case of a tie, priority is given to a match.
                if H[i][j] == H[i-1][j-1] + x*_bool_match(a[i-1], b[j-1]):
                    tb[i][j] = (-1, -1)
                elif H[i][j] == H[i-1][j] + s:
                    tb[i][j] = (-1, 0)
                elif H[i][j] == H[i][j-1] + s:
                    tb[i][j] = (0, -1)

    elif method == 'match_mismatch':
        for i in range(1, n1+1):
            for j in range(1, n2+1):
                H[i][j] = max(H[i-1][j] + s,
                              H[i][j-1] + s,
                              H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,x))
                #Fill in a traceback matrix
                #In case of a tie, priority is given to a match.
                if H[i][j] == (H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,x)):
                    tb[i][j] = (-1, -1)
                elif H[i][j] == H[i-1][j] + s:
                    tb[i][j] = (-1, 0)
                elif H[i][j] == H[i][j-1] + s:
                    tb[i][j] = (0, -1)

    return H, tb

def NW_match_mismatch(a, b, m=1, x=-1, s=-1):
    """Take 2 strings, a and b, of lengths n1 and n2, and compute NW edit
    distance between them
    Compute a matrix S of shape n1+1 by n2+1, and recursively fill it.

    Params
    ------
    a, b: input strings
    m: int, match score
    x: int, mismatch score
    s: int, 'gap' score

    Returns
    -------
    H: edit distance matrix
    tr: traceback matrix
    """
    n1 = len(a)
    n2 = len(b)
    H = np.zeros([n1+1,n2+1])
    dt = np.dtype("i4, i4")
    tb = np.zeros([n1+1,n2+1], dtype=dt)

    for i in range(1,n1+1):
        H[i][0] = i*s
    for j in range(1,n2+1):
        H[0][j] = j*s

    for i in range(1, n1+1):
        for j in range(1, n2+1):
            H[i][j] = max(H[i-1][j] + s,
                          H[i][j-1] + s,
                          H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,x))
            #Fill in a traceback matrix
            #In case of a tie, priority is given to a match.
            if H[i][j] == (H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,x)):
                tb[i][j] = (-1, -1)
            elif H[i][j] == H[i-1][j] + s:
                tb[i][j] = (-1, 0)
            elif H[i][j] == H[i][j-1] + s:
                tb[i][j] = (0, -1)

    return H, tb


def smithwaterman(a, b, m=1, s=-1, x=-1):
    """Basic Smithwaterman algo. Initializes the first row and column as 0.
    Usage: Finds the best position of a short string, a, in a long string, b.

    Params
    ------
    a: "query" string. Ideally, should be shorter than b, but not necessarily.
    b: "target" string.
    m: int >= 0; match cost. Positive, so this isn't a cost.
    s: int <= 0; substitution cost.
    x: int <= 0; indel cost.

    Returns
    --–----
    H: array of shape (len(a)+1, len(b)+1)
    """
    n1 = len(a)
    n2 = len(b)
    H = np.zeros([n1+1,n2+1])
    dt = np.dtype("i4, i4")
    tb = np.zeros([n1+1,n2+1], dtype=dt)

    for i in range(1,n1+1):
        H[i][0] = 0
    for j in range(1,n2+1):
        H[0][j] = 0

    for i in range(1, n1+1):
        for j in range(1, n2+1):
            H[i][j] = max(H[i-1][j] + s,
                          H[i][j-1] + s,
                          H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,x),
                         0)
            #Fill in a traceback matrix
            #In case of a tie, priority is given to a match.
            if H[i][j] == (H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,x)):
                tb[i][j] = (-1, -1)
            elif H[i][j] == H[i-1][j] + s:
                tb[i][j] = (-1, 0)
            elif H[i][j] == H[i][j-1] + s:
                tb[i][j] = (0, -1)

    return H


def smithwaterman_mod(a, b, m=1, s=-1, x=-1):
    """Modified such that only the first col is initialized at 0. I forget
    if this makes any difference to initializing both the first row and col at
    all zeros.
    Usage: Finds the best position of a short string, a, in a long string, b.

    Params
    ------
    a: "query" string. Ideally, should be shorter than b, but not necessarily.
    b: "target" string.
    m: int >= 0; match cost. Positive, so this isn't a cost.
    s: int <= 0; substitution cost.
    x: int <= 0; indel cost.

    Returns
    --–----
    H: array of shape (len(a)+1, len(b)+1)
    """
    n1 = len(a); n2 = len(b)
    H = np.zeros([n1+1,n2+1])
    dt = np.dtype("i4, i4")
    tb = np.zeros([n1+1,n2+1], dtype=dt)

    for i in range(1,n1+1):
        H[i][0] = i*s
    for j in range(1,n2+1):
        H[0][j] = 0

    for i in range(1, n1+1):
        for j in range(1, n2+1):
            H[i][j] = max(H[i-1][j] + s,
                          H[i][j-1] + s,
                          H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,x),
                         0)
            #Fill in a traceback matrix
            #In case of a tie, priority is given to a match.
            if H[i][j] == (H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,x)):
                tb[i][j] = (-1, -1)
            elif H[i][j] == H[i-1][j] + s:
                tb[i][j] = (-1, 0)
            elif H[i][j] == H[i][j-1] + s:
                tb[i][j] = (0, -1)

    return H



def NW_kt(a, b, m=0, ins=1, dl=1, s=1, verbose=False):
    """The version from Knowledge Tech course."""
    n1 = len(a)
    n2 = len(b)
    H = np.zeros([n1+1,n2+1])
    dt = np.dtype("i4, i4")
    tb = np.zeros([n1+1,n2+1], dtype=dt)

    if verbose:
        print("{m, i, d, s} = (%s, %s, %s, %s)"% (m, ins, dl, s))

    for i in range(1,n1+1):
        H[i][0] = i*ins
    for j in range(1,n2+1):
        H[0][j] = j*dl

    for i in range(1, n1+1):
        for j in range(1, n2+1):
            H[i][j] = min(H[i-1][j] + dl,
                          H[i][j-1] + ins,
                          H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,s))
            #Fill in a traceback matrix
            #In case of a tie, priority is given to a match.
            if H[i][j] == (H[i-1][j-1] + _match_mismatch(a[i-1],b[j-1],m,s)):
                tb[i][j] = (-1, -1)
            elif H[i][j] == H[i-1][j] + dl:
                tb[i][j] = (-1, 0)
            elif H[i][j] == H[i][j-1] + ins:
                tb[i][j] = (0, -1)

    return H


def _bool_match(x1,x2):
    """returns 1 if the single str characters x1 == x2,
    0 otherwise
    """
    match = 0
    if x1 == x2:
        match = 1

    return match


def _match_mismatch(x1, x2, m, x):
    """Returns m if a single str characters x1 == x2,
    x otherwise
    """
    score = 0
    if x1 == x2:
        score = m
    else:
        score = x
    return score


def replace_chars(char_ls, new_char, my_string):
    """Given my_string, replaces all occurrences of characters in char_ls with
    new_char.
    e.g. my_string = "the_quick?brown//fox!jumps"
    char_ls = ['_', '?', '//', '!']
    replace_chars(char_ls, " ", my_string)
    >> the quick brown fox jumps
    """
    for ch in char_ls:
        my_string = my_string.replace(ch, new_char)

    return my_string


def raxml_to_figtree(tree_string):
    """WIP.
    Parses raxml output, with bootstrap support values, into a format that
    Figtree can understand.
    """
    pattern = re.compile(r'([:]\d+[.]\d+)[[](\d+)[]]')
    matches_ls = re.findall(pattern, tree_string)

    for line in matches_ls:
        x, y = line
        old_str = x + "[" + y + "]"
        new_str = y + x
        tree_string = tree_string.replace(old_str, new_str)

    return tree_string

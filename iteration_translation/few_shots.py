translate_all_shots = [
    {
        "python_prompt": "Write a python function to sum the length of the names of a given list of names after removing the names that start with a lowercase letter.",
        "python_signature": "",
        "python_code": "def sample_nam(sample_names):\n  sample_names=list(filter(lambda el:el[0].isupper() and el[1:].islower(),sample_names))\n  return len(''.join(sample_names))",
        "python_test": "\n".join(["assert sample_nam(['sally', 'Dylan', 'rebecca', 'Diana', 'Joanne', 'keith'])==16", "assert sample_nam([\"php\", \"res\", \"Python\", \"abcd\", \"Java\", \"aaa\"])==10", "assert sample_nam([\"abcd\", \"Python\", \"abba\", \"aba\"])==6"]),
        "c_prompt": "// Write a C function to sum the length of the names of a given vector of names after removing the names that start with a lowercase letter.\nlong sample_nam(char** sample_names, int size);\n",
        "c_signature": "long sample_nam(char** sample_names, int size);",
        "c_code": "#include <ctype.h>\n#include <string.h>\n#include <assert.h>\nint sample_nam(char** sample_names, int count) {\n    int len = 0;\n    for (int i = 0; i < count; i++) {\n        if (isupper(sample_names[i][0]) && islower(sample_names[i][1])) {\n            len += strlen(sample_names[i]);\n        }\n    }\n    return len;\n}\n",
        "c_test": "int main() {\n    char* sample_names1[] = {\"sally\", \"Dylan\", \"rebecca\", \"Diana\", \"Joanne\", \"keith\"};\n    assert(sample_nam(sample_names1, 6) == 16);\n\n    char* sample_names2[] = {\"php\", \"res\", \"Python\", \"abcd\", \"Java\", \"aaa\"};\n    assert(sample_nam(sample_names2, 6) == 10);\n\n    char* sample_names3[] = {\"abcd\", \"Python\", \"abba\", \"aba\"};\n    assert(sample_nam(sample_names3, 4) == 6);\n}\n"
    },
    {
        "python_prompt": "Write a function to extract values between quotation marks of the given string by using regex.",
        "python_signature": "",
        "python_code": "import re\r\ndef extract_quotation(text1):\r\n  return (re.findall(r'\"(.*?)\"', text1))",
        "python_test": "\n".join(["assert extract_quotation('Cortex \"A53\" Based \"multi\" tasking \"Processor\"') == ['A53', 'multi', 'Processor']", "assert extract_quotation('Cast your \"favorite\" entertainment \"apps\"') == ['favorite', 'apps']", "assert extract_quotation('Watch content \"4k Ultra HD\" resolution with \"HDR 10\" Support') == ['4k Ultra HD', 'HDR 10']"]),
        "c_prompt": "// Write a C function to extract values between quotation marks \" \" of the given string.\nchar** extract_quotation(char* text1, int* size);\n",
        "c_signature": "char** extract_quotation(char* text1, int* size);",
        "c_code": "#define MAX_QUOTATIONS 100\n#define MAX_QUOTATION_LENGTH 100\nchar** extract_quotation(char* text1, int* size) {\n    char** quotations = (char**)malloc(MAX_QUOTATIONS * sizeof(char*));\n    *size = 0; // Initialize the size to 0\n    char* start = text1;\n    char* end;\n\n    while ((start = strchr(start, '\"')) != NULL) {\n        start++; // Move past the opening quote\n        end = strchr(start, '\"'); // Find the closing quote\n        if (end == NULL) {\n            break; // No closing quote found\n        }\n\n        // Allocate memory for the extracted quotation\n        quotations[*size] = (char*)malloc((end - start + 1) * sizeof(char));\n        strncpy(quotations[*size], start, end - start);\n        quotations[*size][end - start] = '\\0'; // Null-terminate the string\n        (*size)++; // Increment the size\n\n        start = end + 1; // Move past the closing quote\n    }\n\n    return quotations;\n}",
        "c_test": "void free_quotations(char** quotations, int size) {\n    for (int i = 0; i < size; i++) {\n        free(quotations[i]);\n    }\n    free(quotations);\n}\nint main() {\n    // Test case 1\n    char* text1 = \"Cortex \\\"A53\\\" Based \\\"multi\\\" tasking \\\"Processor\\\"\";\n    int size;\n    char** result = extract_quotation(text1, &size);\n    char* expected1[] = {\"A53\", \"multi\", \"Processor\"};\n    assert(size == 3); // Check the number of extracted quotations\n    for (int i = 0; i < size; i++) {\n        assert(strcmp(result[i], expected1[i]) == 0);\n    }\n    free_quotations(result, size);\n\n    // Test case 2\n    text1 = \"Cast your \\\"favorite\\\" entertainment \\\"apps\\\"\";\n    result = extract_quotation(text1, &size);\n    char* expected2[] = {\"favorite\", \"apps\"};\n    assert(size == 2); // Check the number of extracted quotations\n    for (int i = 0; i < size; i++) {\n        assert(strcmp(result[i], expected2[i]) == 0);\n    }\n    free_quotations(result, size);\n\n    // Test case 3\n    text1 = \"Watch content \\\"4k Ultra HD\\\" resolution with \\\"HDR 10\" Support\";\n    result = extract_quotation(text1, &size);\n    char* expected3[] = {\"4k Ultra HD\", \"HDR 10\"};\n    assert(size == 2); // Check the number of extracted quotations\n    for (int i = 0; i < size; i++) {\n        assert(strcmp(result[i], expected3[i]) == 0);\n    }\n    free_quotations(result, size);\n\n    // Test case 4: No double quotes\n    text1 = \"Watch content '4k Ultra HD' resolution with 'HDR 10' Support\";\n    result = extract_quotation(text1, &size);\n    assert(size == 0); // No double quotes, so size should be 0\n    free_quotations(result, size);\n\n    return 0;\n}"
    },
    {
        "python_prompt": "Write a function to sort a given list of strings of numbers numerically.",
        "python_signature": "",
        "python_code": "def sort_numeric_strings(nums_str):\r\n    result = [int(x) for x in nums_str]\r\n    result.sort()\r\n    return result",
        "python_test": "\n".join(["assert sort_numeric_strings( ['4','12','45','7','0','100','200','-12','-500'])==[-500, -12, 0, 4, 7, 12, 45, 100, 200]", "assert sort_numeric_strings(['2','3','8','4','7','9','8','2','6','5','1','6','1','2','3','4','6','9','1','2'])==[1, 1, 1, 2, 2, 2, 2, 3, 3, 4, 4, 5, 6, 6, 6, 7, 8, 8, 9, 9]", "assert sort_numeric_strings(['1','3','5','7','1', '3','13', '15', '17','5', '7 ','9','1', '11'])==[1, 1, 1, 3, 3, 5, 5, 7, 7, 9, 11, 13, 15, 17]"]),
        "c_prompt": "// Write a function to sort a given vector of strings of numbers numerically.\n long* sort_numeric_strings(char** nums_str, int size);\n",
        "c_signature": "long* sort_numeric_strings(char** nums_str, int size);",
        "c_code": "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <assert.h>\nint sort_numeric_strings(char **nums_str, int size) {\n    int *result = malloc(size * sizeof(int));\n    for (int i = 0; i < size; ++i) {\n        result[i] = atoi(nums_str[i]);\n    }\n    for (int i = 0; i < size - 1; ++i) {\n        for (int j = 0; j < size - i - 1; ++j) {\n            if (result[j] > result[j + 1]) {\n                int temp = result[j];\n                result[j] = result[j + 1];\n                result[j + 1] = temp;\n            }\n        }\n    }\n    for (int i = 0; i < size; ++i) {\n        nums_str[i] = malloc(12 * sizeof(char));\n        sprintf(nums_str[i], \"%d\", result[i]);\n    }\n    free(result);\n    return 0;\n}\n",
        "c_test": "\nint main() {\n    char *input1[] = {\"4\", \"12\", \"45\", \"7\", \"0\", \"100\", \"200\", \"-12\", \"-500\"};\n    int size1 = sizeof(input1) / sizeof(input1[0]);\n    sort_numeric_strings(input1, size1);\n    char *expected1[] = {\"-500\", \"-12\", \"0\", \"4\", \"7\", \"12\", \"45\", \"100\", \"200\"};\n    for (int i = 0; i < size1; ++i) {\n        assert(strcmp(input1[i], expected1[i]) == 0);\n        free(input1[i]);\n    }\n\n    char *input2[] = {\"2\", \"3\", \"8\", \"4\", \"7\", \"9\", \"8\", \"2\", \"6\", \"5\", \"1\", \"6\", \"1\", \"2\", \"3\", \"4\", \"6\", \"9\", \"1\", \"2\"};\n    int size2 = sizeof(input2) / sizeof(input2[0]);\n    sort_numeric_strings(input2, size2);\n    char *expected2[] = {\"1\", \"1\", \"1\", \"2\", \"2\", \"2\", \"2\", \"3\", \"3\", \"4\", \"4\", \"5\", \"6\", \"6\", \"6\", \"7\", \"8\", \"8\", \"9\", \"9\"};\n    for (int i = 0; i < size2; ++i) {\n        assert(strcmp(input2[i], expected2[i]) == 0);\n        free(input2[i]);\n    }\n\n    char *input3[] = {\"1\", \"3\", \"5\", \"7\", \"1\", \"3\", \"13\", \"15\", \"17\", \"5\", \"7\", \"9\", \"1\", \"11\"};\n    int size3 = sizeof(input3) / sizeof(input3[0]);\n    sort_numeric_strings(input3, size3);\n    char *expected3[] = {\"1\", \"1\", \"1\", \"3\", \"3\", \"5\", \"5\", \"7\", \"7\", \"9\", \"11\", \"13\", \"15\", \"17\"};\n    for (int i = 0; i < size3; ++i) {\n        assert(strcmp(input3[i], expected3[i]) == 0);\n        free(input3[i]);\n    }\n    return 0;\n}\n"
    },
    {
        "python_prompt": "Write a function to find maximum possible sum of disjoint pairs for the given array of integers and a number k.",
        "python_signature": "",
        "python_code": "def max_sum_pair_diff_lessthan_K(arr, N, K): \n\tarr.sort() \n\tdp = [0] * N \n\tdp[0] = 0\n\tfor i in range(1, N): \n\t\tdp[i] = dp[i-1] \n\t\tif (arr[i] - arr[i-1] < K): \r\n\t\t\tif (i >= 2): \r\n\t\t\t\tdp[i] = max(dp[i], dp[i-2] + arr[i] + arr[i-1]); \r\n\t\t\telse: \r\n\t\t\t\tdp[i] = max(dp[i], arr[i] + arr[i-1]); \n\treturn dp[N - 1]",
        "python_test": "\n".join(["assert max_sum_pair_diff_lessthan_K([3, 5, 10, 15, 17, 12, 9], 7, 4) == 62", "assert max_sum_pair_diff_lessthan_K([5, 15, 10, 300], 4, 12) == 25", "assert max_sum_pair_diff_lessthan_K([1, 2, 3, 4, 5, 6], 6, 6) == 21"]),
        "c_prompt": "// Write a function to sort each subvector of strings in a given vector of vectors.\nchar*** sort_sublists(char*** list1, int outer_size, int* inner_sizes);\n",
        "c_signature": "char*** sort_sublists(char*** list1, int outer_size, int* inner_sizes);",
        "c_code": "#include <stdlib.h>\n#include <string.h>\nint compare_strings(const void* a, const void* b) {\n    return strcmp(*(const char**)a, *(const char**)b);\n}\n\n// Function to sort each subvector of strings in a given vector of vectors\nchar*** sort_sublists(char*** list, int outer_size, int* inner_sizes) {\n    // Allocate memory for the sorted vector of vectors\n    char*** sorted_list = (char***)malloc(outer_size * sizeof(char**));\n    if (!sorted_list) {\n        perror(\"Failed to allocate memory\");\n        exit(EXIT_FAILURE);\n    }\n\n    // Sort each subvector\n    for (int i = 0; i < outer_size; ++i) {\n        // Allocate memory for the sorted subvector\n        sorted_list[i] = (char**)malloc(inner_sizes[i] * sizeof(char*));\n        if (!sorted_list[i]) {\n            perror(\"Failed to allocate memory\");\n            exit(EXIT_FAILURE);\n        }\n\n        // Copy the original subvector to the sorted subvector\n        memcpy(sorted_list[i], list[i], inner_sizes[i] * sizeof(char*));\n\n        // Sort the subvector\n        qsort(sorted_list[i], inner_sizes[i], sizeof(char*), compare_strings);\n    }\n\n    return sorted_list;\n}",
        "c_test": "void free_sorted_list(char*** sorted_list, int outer_size) {\n    for (int i = 0; i < outer_size; ++i) {\n        free(sorted_list[i]);\n    }\n    free(sorted_list);\n}\nint main() {\n    // Test case 1\n    char* list0[] = {\"green\", \"orange\"};\n    char* list1[] = {\"black\", \"white\"};\n    char* list2[] = {\"white\", \"black\", \"orange\"};\n    int sizes[] = {2, 2, 3};\n    char* expected0[] = {\"green\", \"orange\"};\n    char* expected1[] = {\"black\", \"white\"};\n    char* expected2[] = {\"black\", \"orange\", \"white\"};\n    char** lists[] = {list0, list1, list2};\n\n    char*** sorted_lists = sort_sublists(lists, 3, sizes);\n    for (int i = 0; i < 2; ++i) {\n        assert(strcmp(sorted_lists[0][i], expected0[i]) == 0);\n        assert(strcmp(sorted_lists[1][i], expected1[i]) == 0);\n    }\n    for (int i = 0; i < 3; ++i) {\n        assert(strcmp(sorted_lists[2][i], expected2[i]) == 0);\n    }\n    free_sorted_list(sorted_lists, 3);\n\n    // Test case 2\n    char* list3[] = {\"green\", \"orange\"};\n    char* list4[] = {\"black\"};\n    char* list5[] = {\"green\", \"orange\"};\n    char* list6[] = {\"white\"};\n    char* expected3[] = {\"green\", \"orange\"};\n    char* expected4[] = {\"black\"};\n    char* expected5[] = {\"green\", \"orange\"};\n    char* expected6[] = {\"white\"};\n    char** lists2[] = {list3, list4, list5, list6};\n    int sizes2[] = {2, 1, 2, 1};\n\n    sorted_lists = sort_sublists(lists2, 4, sizes2);\n    for (int i = 0; i < 2; ++i) {\n        assert(strcmp(sorted_lists[0][i], expected3[i]) == 0);\n        assert(strcmp(sorted_lists[2][i], expected5[i]) == 0);\n    }\n    assert(strcmp(sorted_lists[1][0], expected4[0]) == 0);\n    assert(strcmp(sorted_lists[3][0], expected6[0]) == 0);\n    free_sorted_list(sorted_lists, 4);\n\n    // Test case 3\n    char* list7[] = {\"a\", \"b\"};\n    char* list8[] = {\"d\", \"c\"};\n    char* list9[] = {\"g\", \"h\"};\n    char* list10[] = {\"f\", \"e\"};\n    char* expected7[] = {\"a\", \"b\"};\n    char* expected8[] = {\"c\", \"d\"};\n    char* expected9[] = {\"g\", \"h\"};\n    char* expected10[] = {\"e\", \"f\"};\n    char** lists3[] = {list7, list8, list9, list10};\n    int sizes3[] = {2, 2, 2, 2};\n\n    sorted_lists = sort_sublists(lists3, 4, sizes3);\n    for (int i = 0; i < 2; ++i) {\n        assert(strcmp(sorted_lists[0][i], expected7[i]) == 0);\n        assert(strcmp(sorted_lists[1][i], expected8[i]) == 0);\n        assert(strcmp(sorted_lists[2][i], expected9[i]) == 0);\n        assert(strcmp(sorted_lists[3][i], expected10[i]) == 0);\n    }\n    free_sorted_list(sorted_lists, 4);\n\n    return 0;\n}\n"
    },
    {
        "python_prompt": "Write a function to find the n - expensive price items from a given dataset using heap queue algorithm.",
        "python_signature": "",
        "python_code": "import heapq\r\ndef expensive_items(items,n):\r\n  expensive_items = heapq.nlargest(n, items, key=lambda s: s['price'])\r\n  return expensive_items",
        "python_test": "\n".join(["assert expensive_items([{'name': 'Item-1', 'price': 101.1},{'name': 'Item-2', 'price': 555.22}],1)==[{'name': 'Item-2', 'price': 555.22}]", "assert expensive_items([{'name': 'Item-1', 'price': 101.1},{'name': 'Item-2', 'price': 555.22}, {'name': 'Item-3', 'price': 45.09}],2)==[{'name': 'Item-2', 'price': 555.22},{'name': 'Item-1', 'price': 101.1}]", "assert expensive_items([{'name': 'Item-1', 'price': 101.1},{'name': 'Item-2', 'price': 555.22}, {'name': 'Item-3', 'price': 45.09},{'name': 'Item-4', 'price': 22.75}],1)==[{'name': 'Item-2', 'price': 555.22}]"]),
        "c_prompt": "// Write a function to find the n most expensive items in a given dataset.\ntypedef struct {\n    char* name;\n    float value;\n} Item;\n\nItem* expensive_items(Item* items, int size, int n, int* new_size);\n",
        "c_signature": "typedef struct {\n    char* name;\n    float value;\n} Item;\n\nItem* expensive_items(Item* items, int size, int n, int* new_size);",
        "c_code": "typedef struct {\n    char* name;\n    float value;\n} Item;\n\n// Function to find the n most expensive items in the dataset.\nint compare_items_qsort(const void* a, const void* b) {\n    Item* itemA = (Item*)a;\n    Item* itemB = (Item*)b;\n    // Sort in descending order (most expensive first)\n    if (itemA->value < itemB->value) return 1;\n    if (itemA->value > itemB->value) return -1;\n    return 0; // If values are equal\n}\n\n// Function to find the n most expensive items (using qsort for efficiency).\nItem* expensive_items(Item* items, int size, int n, int* new_size) {\n\n     if (items == NULL || size <= 0 || n <= 0 || new_size == NULL) {\n        *new_size = 0;\n        return NULL; // Handle invalid input\n    }\n\n\n    //Use qsort for in-place sorting\n    qsort(items, size, sizeof(Item), compare_items_qsort);\n\n\n    //Determine the new size\n     *new_size = (n < size) ? n : size;\n\n\n    //Allocate memory for the result and copy.\n      Item* result = (Item*)malloc(*new_size * sizeof(Item));\n     if (result == NULL) {\n        perror(\"Memory allocation failed\");\n        *new_size = 0;\n        return NULL;\n    }\n\n\n    for(int i=0; i < *new_size; ++i)\n    {\n        result[i].name = strdup(items[i].name);\n          if (result[i].name == NULL) { // Handle strdup failure\n            perror(\"strdup failed\");\n            // Clean up and return\n            free_items(result,i); //Free allocated resources.\n            *new_size = 0;\n            return NULL;\n\n        }\n\n\n        result[i].value = items[i].value;\n    }\n\n    return result;\n\n}",
        "c_test": "bool compare_items(const Item* arr1, int size1, const Item* arr2, int size2) {\n    if (size1 != size2) {\n        return false;\n    }\n    for (int i = 0; i < size1; i++) {\n        if (strcmp(arr1[i].name, arr2[i].name) != 0 || arr1[i].value != arr2[i].value) { // Corrected: String comparison\n            return false;\n        }\n    }\n    return true;\n}\n\n//Helper function to free items.\nvoid free_items(Item *items, int size)\n{\n    for(int i=0; i < size; ++i) free(items[i].name);\n    free(items);\n\n}\n\nint main() {\n      Item items1[] = {{\"Item-1\", 101.1f}, {\"Item-2\", 555.22f}};\n    Item expected1[] = {{\"Item-2\", 555.22f}};\n    int n1 = 1;\n    int new_size1;\n\n\n    Item *result1 = expensive_items(items1, sizeof(items1)/ sizeof(items1[0]), n1, &new_size1);\n    assert(compare_items(result1, new_size1, expected1, sizeof(expected1)/ sizeof(expected1[0])));\n\n     free_items(result1,new_size1);\n\n    // Test case 2 (Corrected and Expanded)\n    Item items2[] = {{\"Item-1\", 101.1f}, {\"Item-2\", 555.22f}, {\"Item-3\", 45.09f}};\n    Item expected2[] = {{\"Item-2\", 555.22f}, {\"Item-1\", 101.1f}};\n    int n2 = 2;  // Request the top 2 items\n    int new_size2;\n\n\n    Item *result2 = expensive_items(items2, sizeof(items2)/ sizeof(items2[0]), n2, &new_size2);\n     assert(compare_items(result2, new_size2, expected2, sizeof(expected2)/ sizeof(expected2[0])));\n\n    free_items(result2,new_size2);\n\n\n\n    // Test case 3  (Corrected)\n    Item items3[] = {{\"Item-1\", 101.1f}, {\"Item-2\", 555.22f}, {\"Item-3\", 45.09f}, {\"Item-4\", 22.75f}};\n    Item expected3[] = {{\"Item-2\", 555.22f}};\n    int n3 = 1;  // Request only top 1.\n      int new_size3;\n\n     Item *result3 = expensive_items(items3, sizeof(items3)/ sizeof(items3[0]), n3, &new_size3);\n    assert(compare_items(result3, new_size3, expected3, sizeof(expected3)/ sizeof(expected3[0])));\n\n      free_items(result3,new_size3);\n\n\n\n    printf(\"All test cases passed!\n\");\n    return 0;\n}"
    },
    {
        "python_prompt": "Write a python function to find the minimum difference between any two elements in a given array.",
        "python_signature": "",
        "python_code": "def find_Min_Diff(arr,n): \r\n    arr = sorted(arr) \r\n    diff = 10**20 \r\n    for i in range(n-1): \r\n        if arr[i+1] - arr[i] < diff: \r\n            diff = arr[i+1] - arr[i]  \r\n    return diff ",
        "python_test": "\n".join(["assert find_Min_Diff((1,5,3,19,18,25),6) == 1", "assert find_Min_Diff((4,3,2,6),4) == 1", "assert find_Min_Diff((30,5,20,9),4) == 4"]),
        "c_prompt": "// Write a C function to find the minimum difference between any two elements in a given array.\nlong find_min_diff(long* arr, long n);\n",
        "c_signature": "long find_min_diff(long* arr, long n);",
        "c_code": "#include <stdio.h>\n#include <stdlib.h>\nint compare(const void *a, const void *b) {\n    return (*(long*)a - *(long*)b);\n}\nint find_min_diff(long arr[], int n) {\n    qsort(arr, n, sizeof(long), compare);\n    long diff = 10e20;\n    for (int i = 0; i < n - 1; i++) {\n        if (arr[i + 1] - arr[i] < diff) {\n            diff = arr[i + 1] - arr[i];\n        }\n    }\n    return diff;\n}\n", "code": "#include <stdio.h>\n#include <stdlib.h>\nint compare(const void *a, const void *b);\nint find_min_diff(long arr[], int n) {\n    qsort(arr, n, sizeof(long), compare);\n    long diff = 10e20;\n    for (int i = 0; i < n - 1; i++) {\n        if (arr[i + 1] - arr[i] < diff) {\n            diff = arr[i + 1] - arr[i];\n        }\n    }\n    return diff;\n}\nint compare(const void *a, const void *b) {\n    return (*(long*)a - *(long*)b);\n}\nint main() {\n    long arr1[] = {1, 5, 3, 19, 18, 25};\n    assert(find_min_diff(arr1, 6) == 1);\n    \n    long arr2[] = {4, 3, 2, 6};\n    assert(find_min_diff(arr2, 4) == 1);\n    \n    long arr3[] = {30, 5, 20, 9};\n    assert(find_min_diff(arr3, 4) == 4);\n    \n    return 0;\n}\n",
        "c_test": "\nint main() {\n    long arr1[] = {1, 5, 3, 19, 18, 25};\n    assert(find_min_diff(arr1, 6) == 1);\n    \n    long arr2[] = {4, 3, 2, 6};\n    assert(find_min_diff(arr2, 4) == 1);\n    \n    long arr3[] = {30, 5, 20, 9};\n    assert(find_min_diff(arr3, 4) == 4);\n    \n    return 0;\n}\n"
    },
    {
        "python_prompt": "Write a function to check if the letters of a given string can be rearranged so that two characters that are adjacent to each other are different.",
        "python_signature": "",
        "python_code": "import heapq\r\nfrom collections import Counter\r\ndef rearange_string(S):\r\n    ctr = Counter(S)\r\n    heap = [(-value, key) for key, value in ctr.items()]\r\n    heapq.heapify(heap)\r\n    if (-heap[0][0]) * 2 > len(S) + 1: \r\n        return \"\"\r\n    ans = []\r\n    while len(heap) >= 2:\r\n        nct1, char1 = heapq.heappop(heap)\r\n        nct2, char2 = heapq.heappop(heap)\r\n        ans.extend([char1, char2])\r\n        if nct1 + 1: heapq.heappush(heap, (nct1 + 1, char1))\r\n        if nct2 + 1: heapq.heappush(heap, (nct2 + 1, char2))\r\n    return \"\".join(ans) + (heap[0][1] if heap else \"\")",
        "python_test": "\n".join(["assert rearange_string(\"aab\")==('aba')", "assert rearange_string(\"aabb\")==('abab')", "assert rearange_string(\"abccdd\")==('cdabcd')"]),
        "c_prompt": "// Write a C function to check if the letters of a given string can be rearranged so that two characters that are adjacent to each other are different.\nchar* rearange_string(char* S);",
        "c_signature": "char* rearange_string(char* S);",
        "c_code": "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <assert.h>\n\n// Max number of characters (assuming ASCII)\n#define MAX_CHARS 128\n\n// Structure to hold character and its count\ntypedef struct {\n    char ch;\n    int count;\n} CharCount;\n\n// Comparison function for qsort to sort in descending order of count\nint compare(const void *a, const void *b) {\n    CharCount *ca = (CharCount *)a;\n    CharCount *cb = (CharCount *)b;\n    return cb->count - ca->count;\n}\n\nchar* rearange_string(char* S) {\n    int len = strlen(S);\n    if (len == 0) return strdup(\"\");\n\n    // Count occurrences of each character\n    CharCount counts[MAX_CHARS] = {0};\n    for (int i = 0; i < len; i++) {\n        counts[(unsigned char)S[i]].ch = S[i];\n        counts[(unsigned char)S[i]].count++;\n    }\n\n    // Sort the counts in descending order\n    qsort(counts, MAX_CHARS, sizeof(CharCount), compare);\n\n    // Check if rearrangement is possible\n    if (counts[0].count * 2 > len + 1) {\n        return strdup(\"\");\n    }\n\n    // Allocate memory for the result string\n    char *result = (char *)malloc((len + 1) * sizeof(char));\n    if (result == NULL) {\n        perror(\"Memory allocation failed\");\n        return strdup(\"\");\n    }\n    result[len] = '\\0';\n\n    // Fill the result string by first placing characters at even indices\n    int index = 0;\n    for (int i = 0; i < MAX_CHARS; i++) {\n        while (counts[i].count > 0) {\n            if (index >= len) {\n                index = 1;\n            }\n            result[index] = counts[i].ch;\n            counts[i].count--;\n            index += 2;\n        }\n    }\n\n    return result;\n}",
        "c_test": "int is_valid_rearrangement(const char* input, const char* output) {\n    int in_counts[MAX_CHARS] = {0};\n    int out_counts[MAX_CHARS] = {0};\n\n    int len = strlen(input);\n    if (strlen(output) != len) return 0;\n\n    for (int i = 0; i < len; i++) {\n        in_counts[(unsigned char)input[i]]++;\n        out_counts[(unsigned char)output[i]]++;\n        if (i > 0 && output[i] == output[i - 1]) {\n            return 0;  // Adjacent same characters\n        }\n    }\n\n    for (int i = 0; i < MAX_CHARS; i++) {\n        if (in_counts[i] != out_counts[i]) return 0;\n    }\n\n    return 1;\n}\nint main() {\n    char* result1 = rearange_string(\"aab\");\n    assert(is_valid_rearrangement(result1, \"aba\"));\n    free(result1);\n\n    char* result2 = rearange_string(\"aabb\");\n    assert(is_valid_rearrangement(result2, \"abab\"));\n    free(result2);\n\n    char* result3 = rearange_string(\"abccdd\");\n    assert(is_valid_rearrangement(result3, \"cdabcd\"));\n    free(result3);\n\n    return 0;\n}"
    },
    {
        "python_prompt": "Write a function to find the top k integers that occur most frequently from given lists of sorted and distinct integers using heap queue algorithm.",
        "python_signature": "",
        "python_code": "def func(nums, k):\r\n    import collections\r\n    d = collections.defaultdict(int)\r\n    for row in nums:\r\n        for i in row:\r\n            d[i] += 1\r\n    temp = []\r\n    import heapq\r\n    for key, v in d.items():\r\n        if len(temp) < k:\r\n            temp.append((v, key))\r\n            if len(temp) == k:\r\n                heapq.heapify(temp)\r\n        else:\r\n            if v > temp[0][0]:\r\n                heapq.heappop(temp)\r\n                heapq.heappush(temp, (v, key))\r\n    result = []\r\n    while temp:\r\n        v, key = heapq.heappop(temp)\r\n        result.append(key)\r\n    return result",
        "python_test": "\n".join(["assert func([[1, 2, 6], [1, 3, 4, 5, 7, 8], [1, 3, 5, 6, 8, 9], [2, 5, 7, 11], [1, 4, 7, 8, 12]],3)==[5, 7, 1]", "assert func([[1, 2, 6], [1, 3, 4, 5, 7, 8], [1, 3, 5, 6, 8, 9], [2, 5, 7, 11], [1, 4, 7, 8, 12]],1)==[1]", "assert func([[1, 2, 6], [1, 3, 4, 5, 7, 8], [1, 3, 5, 6, 8, 9], [2, 5, 7, 11], [1, 4, 7, 8, 12]],5)==[6, 5, 7, 8, 1]"]),
        "c_prompt": "// Write a C function to find the top k integers that occur most frequently from given lists of sorted and distinct integers using heap queue algorithm.\nint* func(int** nums, int* sizes, int num_rows, int k, int* result_size);",
        "c_signature": "int* func(int** nums, int* sizes, int num_rows, int k, int* result_size);",
        "c_code": "#include <stdio.h>\n#include <stdlib.h>\n#include <assert.h>\n#include <stdbool.h>\n\n// Structure to hold number and its frequency\ntypedef struct {\n    int num;\n    int freq;\n} NumFreq;\n\n// Comparison function for qsort\ntypedef struct {\n    int num;\n    int freq;\n} FreqEntry;\n\nint compare_freq(const void* a, const void* b) {\n    return ((FreqEntry*)b)->freq - ((FreqEntry*)a)->freq;\n}\n\n// Main function to find top k frequent numbers\nint* func(int** nums, int* sizes, int num_rows, int k, int* result_size) {\n    // Create a frequency map\n    int max_num = 0;\n    for (int i = 0; i < num_rows; i++) {\n        for (int j = 0; j < sizes[i]; j++) {\n            if (nums[i][j] > max_num) {\n                max_num = nums[i][j];\n            }\n        }\n    }\n    int* freq_map = (int*)calloc(max_num + 1, sizeof(int));\n    for (int i = 0; i < num_rows; i++) {\n        for (int j = 0; j < sizes[i]; j++) {\n            freq_map[nums[i][j]]++;\n        }\n    }\n\n    // Count unique numbers\n    int unique_count = 0;\n    for (int i = 0; i <= max_num; i++) {\n        if (freq_map[i] > 0) unique_count++;\n    }\n\n    FreqEntry* all = (FreqEntry*)malloc(unique_count * sizeof(FreqEntry));\n    int idx = 0;\n    for (int i = 0; i <= max_num; i++) {\n        if (freq_map[i] > 0) {\n            all[idx].num = i;\n            all[idx].freq = freq_map[i];\n            idx++;\n        }\n    }\n\n    qsort(all, unique_count, sizeof(FreqEntry), compare_freq);\n\n    *result_size = (k < unique_count) ? k : unique_count;\n    int* result = (int*)malloc(*result_size * sizeof(int));\n    for (int i = 0; i < *result_size; i++) {\n        result[i] = all[i].num;\n    }\n\n    free(all);\n    free(freq_map);\n\n    return result;\n}",
        "c_test": "bool same_elements(int* a, int* b, int n) {\n    int seen[1000] = {0};\n    for (int i = 0; i < n; i++) seen[a[i]]++;\n    for (int i = 0; i < n; i++) seen[b[i]]--;\n    for (int i = 0; i < 1000; i++) {\n        if (seen[i] != 0) return false;\n    }\n    return true;\n}\n\nvoid assert_has_top_k(int* result, int result_size, int* freq_map, int max_val, int k) {\n    // Find actual top k frequencies\n    int freq_list[1000] = {0};\n    for (int i = 0; i <= max_val; i++) freq_list[freq_map[i]]++;\n\n    int current = 1000;\n    int count = 0;\n    int threshold = 0;\n    while (current >= 0) {\n        if (freq_list[current] > 0) {\n            count += freq_list[current];\n            if (count >= k) {\n                threshold = current;\n                break;\n            }\n        }\n        current--;\n    }\n    // Ensure all items in result are >= threshold frequency\n    for (int i = 0; i < result_size; i++) {\n        assert(freq_map[result[i]] >= threshold);\n    }\n}\n\nint main() {\n    // Dynamically allocate 2D array for nums1\n    int** nums1 = (int**)malloc(5 * sizeof(int*));\n    nums1[0] = (int*)malloc(3 * sizeof(int));\n    nums1[0][0] = 1; nums1[0][1] = 2; nums1[0][2] = 6;\n    nums1[1] = (int*)malloc(6 * sizeof(int));\n    nums1[1][0] = 1; nums1[1][1] = 3; nums1[1][2] = 4; nums1[1][3] = 5; nums1[1][4] = 7; nums1[1][5] = 8;\n    nums1[2] = (int*)malloc(6 * sizeof(int));\n    nums1[2][0] = 1; nums1[2][1] = 3; nums1[2][2] = 5; nums1[2][3] = 6; nums1[2][4] = 8; nums1[2][5] = 9;\n    nums1[3] = (int*)malloc(4 * sizeof(int));\n    nums1[3][0] = 2; nums1[3][1] = 5; nums1[3][2] = 7; nums1[3][3] = 11;\n    nums1[4] = (int*)malloc(5 * sizeof(int));\n    nums1[4][0] = 1; nums1[4][1] = 4; nums1[4][2] = 7; nums1[4][3] = 8; nums1[4][4] = 12;\n\n    int sizes1[] = {3, 6, 6, 4, 5};\n    int num_rows1 = 5;\n\n    // Frequency map to use for assertions\n    int max_val = 12;\n    int* freq_map = (int*)calloc(max_val + 1, sizeof(int));\n    for (int i = 0; i < num_rows1; i++) {\n        for (int j = 0; j < sizes1[i]; j++) {\n            freq_map[nums1[i][j]]++;\n        }\n    }\n\n    // Test case 1\n    int k1 = 3;\n    int result_size1;\n    int* result1 = func(nums1, sizes1, num_rows1, k1, &result_size1);\n    assert_has_top_k(result1, result_size1, freq_map, max_val, k1);\n    free(result1);\n\n    // Test case 2\n    int k2 = 1;\n    int result_size2;\n    int* result2 = func(nums1, sizes1, num_rows1, k2, &result_size2);\n    assert_has_top_k(result2, result_size2, freq_map, max_val, k2);\n    free(result2);\n\n    // Test case 3\n    int k3 = 5;\n    int result_size3;\n    int* result3 = func(nums1, sizes1, num_rows1, k3, &result_size3);\n    assert_has_top_k(result3, result_size3, freq_map, max_val, k3);\n    free(result3);\n\n    // Free the dynamically allocated 2D array\n    for (int i = 0; i < 5; i++) {\n        free(nums1[i]);\n    }\n    free(nums1);\n    free(freq_map);\n    return 0;\n}"
    },
]

translate_all_shots = translate_all_shots[:]

translate_apps_shots = [
    {
        "python_prompt": "Two great friends, Eddie John and Kris Cross, are attending the Brackets Are Perfection Conference. They wholeheartedly agree with the main message of the conference and they are delighted with all the new things they learn about brackets. One of these things is a bracket sequence. If you want to do a computation with $+$ and $\times $, you usually write it like so:[ (2 \\times (2 + 1 + 0 + 1) \\times 1) + 3 + 2. ] The brackets are only used to group multiplications and additions together. This means that you can remove all the operators, as long as you remember that addition is used for numbers outside any parentheses! A bracket sequence can then be shortened to[ (\; 2 \; ( \; 2 \; 1 \; 0 \; 1 \; ) \; 1 \; ) \; 3 \; 2. ] That is much better, because it saves on writing all those operators. Reading bracket sequences is easy, too. Suppose you have the following bracket sequence[ 5 \; 2 \; (\; 3 \; 1 \; (\; 2 \; 2 \; ) \; ( \; 3 \; 3 \; ) \; 1 \; ). ] You start with addition, so this is the same as the following:[ 5 + 2 + (\; 3 \; 1 \; (\; 2 \; 2 \; ) \; ( \; 3 \; 3 \; ) \; 1 \; ). ] You know the parentheses group a multiplication, so this is equal to[ 5 + 2 + (3 \times 1 \times (\; 2 \; 2 \; ) \times ( \; 3 \; 3 \; ) \times 1). ] Then there is another level of parentheses: that groups an operation within a multiplication, so the operation must be addition.[ 5 + 2 + (3 \times 1 \times (2 + 2 ) \times (3 + 3) \times 1 ) = 5 + 2 + (3 \times 1 \times 4 \times 6 \times 1) = 5+2 + 72 = 79. ] Since bracket sequences are so much easier than normal expressions with operators, it should be easy to evaluate some big ones. We will even allow you to write a program to do it for you. Note that $(\; )$ is not a valid bracket sequence, nor a subsequence of any valid bracket sequence. -----Input----- - One line containing a single integer $1\leq n\leq 3\cdot 10^5$. - One line consisting of $n$ tokens, each being either (, ), or an integer $0\leq x < 10^9+7$. It is guaranteed that the tokens form a bracket sequence. -----Output----- Output the value of the given bracket sequence. Since this may be very large, you should print it modulo $10^9+7$. -----Examples----- Sample Input 1: 2 2 3 Sample Output 1: 5 Sample Input 2: 8 ( 2 ( 2 1 ) ) 3 Sample Output 2: 9 Sample Input 3: 4 ( 12 3 ) Sample Output 3: 36 Sample Input 4: 6 ( 2 ) ( 3 ) Sample Output 4: 5 Sample Input 5: 6 ( ( 2 3 ) ) Sample Output 5: 5",
        "python_code": "",
        "python_test": "[{'input': '2\n2 3\n', 'output': '5\n'}, {'input': '8\n( 2 ( 2 1 ) ) 3\n', 'output': '9\n'}, {'input': '4\n( 12 3 )\n', 'output': '36\n'}, {'input': '6\n( 2 ) ( 3 )\n', 'output': '5\n'}, {'input': '6\n( ( 2 3 ) )\n', 'output': '5\n'}, {'input': '11\n1 ( 0 ( 583920 ( 2839 82 ) ) )\n', 'output': '1\n'}]",
        "c_signature": "typedef enum { NUMBER, OPEN_PAREN, CLOSE_PAREN } TokenType;\ntypedef struct {\n TokenType type;\n long long value;\n} Token;\n long long evaluate_expression(Token parsed_tokens[], int num_tokens);",
        "c_code": "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <assert.h>\n\n#define MOD 1000000007\n#define MAX_N 300005\n\ntypedef enum {\n    NUMBER,\n    OPEN_PAREN,\n    CLOSE_PAREN\n} TokenType;\n\ntypedef struct {\n    TokenType type;\n    long long value;\n} Token;\n\nlong long values_stack[MAX_N / 2 + 5];\nint depth_stack[MAX_N / 2 + 5];\nint val_sp = 0;\nint depth_sp = 0;\n\nvoid push_val(long long val) { values_stack[val_sp++] = val; }\nlong long pop_val() { return values_stack[--val_sp]; }\nvoid push_depth(int depth) { depth_stack[depth_sp++] = depth; }\nint pop_depth() { return depth_stack[--depth_sp]; }\n\nlong long evaluate_expression(Token parsed_tokens[], int num_tokens) {\n    val_sp = 0;\n    depth_sp = 0;\n    long long current_val = 0;\n    int current_depth = 0;\n\n    for (int i = 0; i < num_tokens; ++i) {\n        Token t = parsed_tokens[i];\n        if (t.type == NUMBER) {\n            if (current_depth % 2 == 0) {\n                current_val = (current_val + t.value) % MOD;\n            } else {\n                current_val = (current_val * t.value) % MOD;\n            }\n        } else if (t.type == OPEN_PAREN) {\n            push_val(current_val);\n            push_depth(current_depth);\n            current_depth++;\n            current_val = (current_depth % 2 == 0) ? 0 : 1;\n        } else if (t.type == CLOSE_PAREN) {\n            long long sub_expression_result = current_val;\n            current_val = pop_val();\n            current_depth = pop_depth();\n            if (current_depth % 2 == 0) {\n                current_val = (current_val + sub_expression_result) % MOD;\n            } else {\n                current_val = (current_val * sub_expression_result) % MOD;\n            }\n        }\n    }\n    return current_val;\n}",
        "c_test": "void parse_raw_tokens(const char* raw_input_tokens[], int num_raw_tokens, Token output_tokens[]) {\n    for (int i = 0; i < num_raw_tokens; ++i) {\n        if (strcmp(raw_input_tokens[i], \"(\") == 0) {\n            output_tokens[i].type = OPEN_PAREN;\n        } else if (strcmp(raw_input_tokens[i], \")\") == 0) {\n            output_tokens[i].type = CLOSE_PAREN;\n        } else {\n            output_tokens[i].type = NUMBER;\n            output_tokens[i].value = atoll(raw_input_tokens[i]);\n        }\n    }\n}\n\nint main() {\n    Token test_tokens_buffer[MAX_N];\n    const char* tc1_raw[] = {\"2\", \"3\"};\n    parse_raw_tokens(tc1_raw, 2, test_tokens_buffer);\n    assert(evaluate_expression(test_tokens_buffer, 2) == 5);\n\n    const char* tc2_raw[] = {\"(\", \"2\", \"(\", \"2\", \"1\", \")\", \")\", \"3\"};\n    parse_raw_tokens(tc2_raw, 8, test_tokens_buffer);\n    assert(evaluate_expression(test_tokens_buffer, 8) == 9);\n\n    const char* tc3_raw[] = {\"(\", \"12\", \"3\", \")\"};\n    parse_raw_tokens(tc3_raw, 4, test_tokens_buffer);\n    assert(evaluate_expression(test_tokens_buffer, 4) == 36);\n\n    const char* tc4_raw[] = {\"(\", \"2\", \")\", \"(\", \"3\", \")\"};\n    parse_raw_tokens(tc4_raw, 6, test_tokens_buffer);\n    assert(evaluate_expression(test_tokens_buffer, 6) == 5);\n\n    const char* tc5_raw[] = {\"(\", \"(\", \"2\", \"3\", \")\", \")\"};\n    parse_raw_tokens(tc5_raw, 6, test_tokens_buffer);\n    assert(evaluate_expression(test_tokens_buffer, 6) == 5);\n\n    const char* tc6_raw[] = {\"1\", \"(\", \"0\", \"(\", \"583920\", \"(\", \"2839\", \"82\", \")\", \")\", \")\"};\n    parse_raw_tokens(tc6_raw, 11, test_tokens_buffer);\n    assert(evaluate_expression(test_tokens_buffer, 11) == 1);\n\n    printf(\"All test cases passed.\n\");\n    return 0;\n}"
    },
    {
        "python_prompt": "The grand museum has just announced a large exhibit on jewelry from around the world. In the hopes of his potential future prosperity, the world-renowned thief and master criminal Edward Terrenando has decided to attempt the magnum opus of his career in thievery. Edward is hoping to purloin a large number of jewels from the exhibit at the grand museum. But alas! He must be careful with which jewels to appropriate in order to maximize the total value of jewels stolen. Edward has $k$ knapsacks of size $1$, $2$, $3$, up to $k$, and would like to know for each the maximum sum of values of jewels that can be stolen. This way he can properly weigh risk vs. reward when choosing how many jewels to steal. A knapsack of size $s$ can hold items if the sum of sizes of those items is less than or equal to $s$. If you can figure out the best total value of jewels for each size of knapsack, you can help Edward pull off the heist of the century! -----Input----- Each input will consist of a single test case. Note that your program may be run multiple times on different inputs. The first line of input will consist of two space-separated integers $n$ and $k$, where $n$ ($1 \le n \le 1000000$) is the number of jewels in the exhibit, and $k$ ($1 \le k \le 100000$) is the maximum size of knapsack available to Edward. The next $n$ lines each will describe a jewel. Each line will consist of two space-separated integers $s$ and $v$, where $s$ ($1 \le s \le 300$) is the size of the jewel, and $v$ ($1 \le v \le 10^9$) is its value. Each jewel can only be taken once per knapsack, but each knapsack is an independent problem. -----Output----- Output $k$ integers separated by whitespace. The first integer should be the maximum value of jewels that will fit in a knapsack of size $1$. The second should be the maximum value of jewels in a knapsack of size $2$, and so on. -----Examples----- Sample Input 1: 4 9 2 8 1 1 3 4 5 100 Sample Output 1: 1 8 9 9 100 101 108 109 109 Sample Input 2: 5 7 2 2 3 8 2 7 2 4 3 8 Sample Output 2: 0 7 8 11 15 16 19",
        "python_code": "",
        "python_test": "[{'input': '4 9\n2 8\n1 1\n3 4\n5 100\n', 'output': '1 8 9 9 100 101 108 109 109\n'}, {'input': '5 7\n2 2\n3 8\n2 7\n2 4\n3 8\n', 'output': '0 7 8 11 15 16 19\n'}, {'input': '2 6\n300 1\n300 2\n', 'output': '0 0 0 0 0 0\n'}]",
        "c_signature": "typedef struct { int size; int value; } Jewel;\nvoid solve_knapsack(Jewel* jewels, int n, int k, int* output_dp);",
        "c_code": "#include <string.h>\n#define MAX_K 100005\ntypedef struct { int size; int value; } Jewel;\nint dp[MAX_K]; // 记录容量 i 下的最大价值\nvoid solve_knapsack(Jewel* jewels, int n, int k, int* output_dp) { memset(dp, 0, sizeof(int) * (k + 1)); for (int i = 0; i < n; ++i) { int s = jewels[i].size; int v = jewels[i].value; for (int j = k; j >= s; --j) { if (dp[j - s] + v > dp[j]) { dp[j] = dp[j - s] + v; } } } for (int i = 1; i <= k; ++i) { output_dp[i - 1] = dp[i]; } }",
        "c_test": "Jewel jewels[1000005]; int output[100005]; void parse_input_and_assert(const char* input_str, const char* expected_output_str) { int n, k; const char* p = input_str; sscanf(p, \"%d %d\", &n, &k); // 跳到宝石数据行 while (*p != '\n') ++p; ++p; for (int i = 0; i < n; ++i) { sscanf(p, \"%d %d\", &jewels[i].size, &jewels[i].value); while (*p != '\n') ++p; ++p; } solve_knapsack(jewels, n, k, output); // 构造输出字符串 char result_str[1000000]; char* out = result_str; for (int i = 0; i < k; ++i) { out += sprintf(out, \"%d%c\", output[i], (i == k - 1 ? '\n' : ' ')); } assert(strcmp(result_str, expected_output_str) == 0); } int main() { parse_input_and_assert( \"4 9\n2 8\n1 1\n3 4\n5 100\n\", \"1 8 9 9 100 101 108 109 109\n\" ); parse_input_and_assert(\"5 7\n2 2\n3 8\n2 7\n2 4\n3 8\n\", \"0 7 8 11 15 16 19\n\" ); parse_input_and_assert( \"2 6\n300 1\n300 2\n\", \"0 0 0 0 0 0\n\" ); printf(\"All test cases passed.\n\"); return 0; }",
    },
    {
        "python_prompt": "KenKen is a popular logic puzzle developed in Japan in 2004. It consists of an $n \times n$ grid divided up into various non-overlapping sections, where each section is labeled with an integer target value and an arithmetic operator. The object is to fill in the entire grid with the numbers in the range 1 to $n$ such that - no number appears more than once in any row or column - in each section you must be able to reach the section’s target using the numbers in the section and the section’s arithmetic operator For this problem we are only interested in single sections of a KenKen puzzle, not the entire puzzle. Two examples of sections from an $8 \times 8$ KenKen puzzle are shown below along with some of their possible assignments of digits. Figure C.1 Note that while sections labeled with a subtraction or division operator can consist of only two grid squares, those labeled with addition or multiplication can have any number. Also note that in a $9 \times 9$ puzzle the first example would have two more solutions, each involving the numbers $9$ and $2$. Finally note that in the first solution of the second section you could not swap the $1$ and $4$ in the first row, since that would result in two $1$’s in the same column. You may be wondering: for a given size KenKen puzzle and a given section in the puzzle, how many valid ways are there to fill in the section? Well, stop wondering and start programming! -----Input----- The input will start with a single line of the form $n$ $m$ $t$ $op$, where $n$ is the size of the KenKen puzzle containing the section to be described, $m$ is the number of grid squares in the section, $t$ is the target value and $op$ is either ‘+’, ‘-’, ‘*’ or ‘/’ indicating the arithmetic operator to use for the section. Next will follow $m$ grid locations of the form $r$ $c$, indicating the row and column number of the grid square. These grid square locations will take up one or more lines. All grid squares in a given section will be connected so that you can move from any one square in the section to any other by crossing shared lines between grid squares. The values of $n$, $m$ and $t$ will satisfy $4\leq n\leq 9$, $2 \leq m \leq 10$, $0 < t \le 3 \cdot 10^8$ and $1 \leq r,c \leq n$. -----Output----- Output the number of valid ways in which the section could be filled in for a KenKen puzzle of the given size. -----Examples----- Sample Input 1: 8 2 7 - 1 1 1 2 Sample Output 1: 2 Sample Input 2: 9 2 7 - 1 1 1 2 Sample Output 2: 4",
        "python_code": "",
        "python_test": "[{'input': '8 2 7 -\n1 1 1 2\n', 'output': '2\n'}, {'input': '9 2 7 -\n1 1 1 2\n', 'output': '4\n'}, {'input': '8 3 6 +\n5 2 6 2 5 1\n', 'output': '7\n'}]",
        "c_signature": "int count_valid_kenken_fillings(int _n, int _m, int _target, char _op, int _pos_r[], int _pos_c[]);",
        "c_code": "#include <stdio.h>\n #include <stdlib.h>\n #include <assert.h>\n #include <stdbool.h>\n #define MAX_M 10\n #define MAX_N 9\n int n, m, target; char op; int pos_r[MAX_M], pos_c[MAX_M]; int count = 0; int grid[MAX_N + 1][MAX_N + 1]; bool used_in_row[MAX_N + 1][MAX_N + 1]; bool used_in_col[MAX_N + 1][MAX_N + 1]; int apply_operation(int values[]) { if (op == '+') { int sum = 0; for (int i = 0; i < m; i++) sum += values[i]; return sum; } else if (op == '*') { int prod = 1; for (int i = 0; i < m; i++) prod *= values[i]; return prod; } else if (op == '-') { int a = values[0], b = values[1]; return abs(a - b); } else if (op == '/') { int a = values[0], b = values[1]; if (a % b == 0) return a / b; if (b % a == 0) return b / a; return -1; } return -1; } void dfs(int idx) { if (idx == m) { int vals[MAX_M]; for (int i = 0; i < m; ++i) vals[i] = grid[pos_r[i]][pos_c[i]]; int result = apply_operation(vals); if (result == target) count++; return; } int r = pos_r[idx], c = pos_c[idx]; for (int num = 1; num <= n; ++num) { if (used_in_row[r][num] || used_in_col[c][num]) continue; grid[r][c] = num; used_in_row[r][num] = used_in_col[c][num] = true; dfs(idx + 1); used_in_row[r][num] = used_in_col[c][num] = false; } } int count_valid_kenken_fillings(int _n, int _m, int _target, char _op, int _pos_r[], int _pos_c[]) { n = _n; m = _m; target = _target; op = _op; for (int i = 0; i < m; ++i) { pos_r[i] = _pos_r[i]; pos_c[i] = _pos_c[i]; } count = 0; for (int i = 1; i <= n; ++i) for (int j = 1; j <= n; ++j) used_in_row[i][j] = used_in_col[i][j] = false; dfs(0); return count; }",
        "c_test": "int main() { // Sample Input 1: 8 2 7 - { int r[] = {1, 1}; int c[] = {1, 2}; assert(count_valid_kenken_fillings(8, 2, 7, '-', r, c) == 2); } // Sample Input 2: 9 2 7 - { int r[] = {1, 1}; int c[] = {1, 2}; assert(count_valid_kenken_fillings(9, 2, 7, '-', r, c) == 4); } // Sample Input 3: 8 3 6 + { int r[] = {5, 6, 5}; int c[] = {2, 2, 1}; assert(count_valid_kenken_fillings(8, 3, 6, '+', r, c) == 7); }\n return 0; }",
    },
    {
        "python_prompt": "It is a well-known fact that if you mix up the letters of a word, while leaving the first and last letters in their places, words still remain readable. For example, the sentence “tihs snetncee mkaes prfecet sesne”, makes perfect sense to most people. If you remove all spaces from a sentence, it still remains perfectly readable, see for example: “thissentencemakesperfectsense”, however if you combine these two things, first shuffling, then removing spaces, things get hard. The following sentence is harder to decipher: “tihssnetnceemkaesprfecetsesne”. You are given a sentence in the last form, together with a dictionary of valid words and are asked to decipher the text. -----Input----- - One line with a string $s$: the sentence to decipher. The sentence consists of lowercase letters and has a length of at least $1$ and at most $1000$ characters. - One line with an integer $n$ with $1 \le n \le 10000$: the number of words in the dictionary. - $n$ lines with one word each. A word consists of lowercase letters and has a length of at least $1$ and at most $100$ characters. All the words are unique. -----Output----- Output one line with the deciphered sentence, if it is possible to uniquely decipher it. Otherwise “impossible” or “ambiguous”, depending on which is the case. -----Examples----- Sample Input 1: tihssnetnceemkaesprfecetsesne 5 makes perfect sense sentence this Sample Output 1: this sentence makes perfect sense Sample Input 2: hitehre 2 there hello Sample Output 2: impossible",
        "python_code": "",
        "python_test": "[{'input': 'tihssnetnceemkaesprfecetsesne\n5\nmakes\nperfect\nsense\nsentence\nthis\n', 'output': 'this sentence makes perfect sense\n'}, {'input': 'hitehre\n2\nthere\nhello\n', 'output': 'impossible\n'}, {'input': 'hitehre\n3\nhi\nthere\nthree\n', 'output': 'ambiguous\n'}]",
        "c_signature": "#define MAX_SENTENCE_LEN 1000\n#define MAX_WORD_LEN 100\n#define MAX_WORDS 10000\n\ntypedef struct {\n    char word[MAX_WORD_LEN + 1];\n} Word;\nint decode(const char *sentence, const Word *words, int n, char *decoded, int *ambiguity);",
        "c_code": "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <assert.h>\n#define MAX_SENTENCE_LEN 1000\n#define MAX_WORD_LEN 100\n#define MAX_WORDS 10000\n\ntypedef struct {\n    char word[MAX_WORD_LEN + 1];\n} Word;\n\nint is_shuffled(const char *s1, const char *s2) {\n    if (strlen(s1) != strlen(s2) || s1[0] != s2[0] || s1[strlen(s1) - 1] != s2[strlen(s2) - 1]) {\n        return 0;\n    }\n    int count[26] = {0};\n    for (int i = 1; i < strlen(s1) - 1; i++) {\n        count[s1[i] - 'a']++;\n        count[s2[i] - 'a']--;\n    }\n    for (int i = 0; i < 26; i++) {\n        if (count[i] != 0) {\n            return 0;\n        }\n    }\n    return 1;\n}\n\nint decode(const char *sentence, const Word *words, int n, char *decoded, int *ambiguity) {\n    int dp[MAX_SENTENCE_LEN + 1][MAX_SENTENCE_LEN + 1];\n    memset(dp, 0, sizeof(dp));\n    dp[0][0] = 1;\n\n    for (int i = 0; i < strlen(sentence); i++) {\n        for (int j = 0; j <= i; j++) {\n            if (dp[j][i - j]) {\n                for (int k = 0; k < n; k++) {\n                    if (i + strlen(words[k].word) <= strlen(sentence) &&\n                        is_shuffled(words[k].word, &sentence[i])) {\n                        int new_end = i + strlen(words[k].word);\n                        if (dp[j + 1][new_end - j - 1]) {\n                            *ambiguity = 1;\n                        }\n                        dp[j + 1][new_end - j - 1] = 1;\n                    }\n                }\n            }\n        }\n    }\n\n    if (!dp[(int)strlen(sentence)][0]) {\n        return 0;\n    }\n\n    if (*ambiguity) {\n        return -1;\n    }\n\n    int index = 0;\n    for (int i = 0; i < strlen(sentence); ) {\n        for (int k = 0; k < n; k++) {\n            if (is_shuffled(words[k].word, &sentence[i])) {\n                strcpy(&decoded[index], words[k].word);\n                index += strlen(words[k].word);\n                decoded[index++] = ' ';\n                i += strlen(words[k].word);\n                break;\n            }\n        }\n    }\n    decoded[index - 1] = '\\0';\n    return 1;\n}",
        "c_test": "int main() {\n{\nconst char *sentence = \"tihssnetnceemkaesprfecetsesne\";\nint n = 5;\nWord words[MAX_WORDS] = {{\"makes\"}, {\"perfect\"}, {\"sense\"}, {\"sentence\"}, {\"this\"}};\nchar decoded[MAX_SENTENCE_LEN * 2];\nint ambiguity = 0;\nint result = decode(sentence, words, n, decoded, &ambiguity);\nif (result == 1) {\nassert(strcmp(decoded, \"this sentence makes perfect sense\") == 0);\n} else if (result == 0) {\nassert(strcmp(\"impossible\", \"impossible\") == 0);\n} else {\nassert(strcmp(\"ambiguous\", \"ambiguous\") == 0);\n}\n}\n{\nconst char *sentence = \"hitehre\";\nint n = 2;\nWord words[MAX_WORDS] = {{\"there\"}, {\"hello\"}};\nchar decoded[MAX_SENTENCE_LEN * 2];\nint ambiguity = 0;\nint result = decode(sentence, words, n, decoded, &ambiguity);\nif (result == 1) {\nassert(strcmp(decoded, \"hitehre\") == 0);\n} else if (result == 0) {\nassert(strcmp(\"impossible\", \"impossible\") == 0);\n} else {\nassert(strcmp(\"ambiguous\", \"ambiguous\") == 0);\n}\n}\n{\nconst char *sentence = \"hitehre\";\nint n = 3;\nWord words[MAX_WORDS] = {{\"hi\"}, {\"there\"}, {\"three\"}};\nchar decoded[MAX_SENTENCE_LEN * 2];\nint ambiguity = 0;\nint result = decode(sentence, words, n, decoded, &ambiguity);\nif (result == 1) {\nassert(strcmp(decoded, \"hitehre\") == 0);\n} else if (result == 0) {\nassert(strcmp(\"impossible\", \"impossible\") == 0);\n} else {\nassert(strcmp(\"ambiguous\", \"ambiguous\") == 0);\n}\n}\nreturn 0;\n}",
    }
]

translate_apps_call_based_shots = [
    {
        "python_prompt": "Given an input string s, reverse the order of the words.\n\nA word is defined as a sequence of non-space characters. The words in s will be separated by at least one space.\n\nReturn a string of the words in reverse order concatenated by a single space.\n\nNote that s may contain leading or trailing spaces or multiple spaces between two words. The returned string should only have a single space separating the words. Do not include any extra spaces.\n\n\nExample 1:\n\nInput: s = \"the sky is blue\"\nOutput: \"blue is sky the\"\nExample 2:\n\nInput: s = \"  hello world  \"\nOutput: \"world hello\"\nExplanation: Your reversed string should not contain leading or trailing spaces.\nExample 3:\n\nInput: s = \"a good   example\"\nOutput: \"example good a\"\nExplanation: You need to reduce multiple spaces between two words to a single space in the reversed string.\nExample 4:\n\nInput: s = \"  Bob    Loves  Alice   \"\nOutput: \"Alice Loves Bob\"\nExample 5:\n\nInput: s = \"Alice does not even like bob\"\nOutput: \"bob like even not does Alice\"\n \n\nConstraints:\n\n1 <= s.length <= 104\ns contains English letters (upper-case and lower-case), digits, and spaces \' \'.\nThere is at least one word in s.",
        "python_signature": "",
        "python_code": "class Solution:\n    def reverseWords(self, s: str) -> str:\n        sLst = s.split()\n        # print(sLst)\n        reverseStr = \"\"\n\n        for i in range(len(sLst)-1,-1,-1):\n            if i == (len(sLst)-1):\n                reverseStr+=sLst[i]\\n            else:\n                reverseStr+=(\" \"+sLst[i])\n        return reverseStr",
        "python_test": "\"inputs\": [[\"the sky is blue\"], [\"  hello world  \"], [\"a good   example\"], [\"  Bob    Loves  Alice   \"], [\"Alice does not even like bob\"]], \"outputs\": [\"blue is sky the\", \"world hello\", \"example good a\", \"Alice Loves Bob\", \"bob like even not does Alice\"]",
        "c_prompt": "",
        "c_signature": "char* reverseWords(char *s);",
        "c_code": "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <assert.h>\n#include <ctype.h>\n\n// Helper function to trim leading and trailing spaces from a string\nchar* trim(char *str) {\n    char *end;\n\n    // Trim leading spaces\n    while (isspace((unsigned char)*str)) str++;\n\n    if (*str == 0)  // All spaces?\n        return str;\n\n    // Trim trailing spaces\n    end = str + strlen(str) - 1;\n    while (end > str && isspace((unsigned char)*end)) end--;\n\n    // Write new null terminator character\n    end[1] = '\\0';\n\n    return str;\n}\n\n// Helper function to split a string by spaces\nchar** split(char *str, int *count) {\n    char *str_copy = strdup(str); // Duplicate the string to avoid modifying the original\n    char *token;\n    char **result = NULL;\n    *count = 0;\n\n    token = strtok(str_copy, \" \");\n    while (token != NULL) {\n        if (strlen(trim(token)) > 0) { // Only add non-empty words\n            (*count)++;\n            result = (char**)realloc(result, sizeof(char*) * (*count));\n            result[(*count) - 1] = strdup(trim(token));\n        }\n        token = strtok(NULL, \" \");\n    }\n    free(str_copy);\n    return result;\n}\n\nchar* reverseWords(char *s) {\n    int wordCount = 0;\n    char **words = split(s, &wordCount);\n    if (wordCount == 0) {\n        return strdup(\"\"); // Handle empty or all-space input\n    }\n\n    // Calculate the required length for the reversed string\n    int totalLength = 0;\n    for (int i = 0; i < wordCount; i++) {\n        totalLength += strlen(words[i]);\n    }\n    totalLength += (wordCount > 0 ? wordCount - 1 : 0); // Add space for separators\n    char *reversedString = (char*)malloc(totalLength + 1);\n    reversedString[0] = '\\0'; // Initialize as an empty string\n\n    for (int i = wordCount - 1; i >= 0; i--) {\n        strcat(reversedString, words[i]);\n        if (i > 0) {\n            strcat(reversedString, \" \");\n        }\n        free(words[i]); // Free the individual word strings\n    }\n    free(words); // Free the array of word pointers\n    return reversedString;\n}",
        "c_test": "void runTest(char *input, char *expected) {\n    char *result = reverseWords(input);\n    assert(strcmp(result, expected) == 0);\n    free(result);\n}\n\nint main() {\n    // Test Cases\n    runTest(\"the sky is blue\", \"blue is sky the\");\n    runTest(\"  hello world  \", \"world hello\");\n    runTest(\"a good   example\", \"example good a\");\n    runTest(\"  Bob    Loves  Alice   \", \"Alice Loves Bob\");\n    runTest(\"Alice does not even like bob\", \"bob like even not does Alice\");\n\n    return 0;\n}"
    },
    {
        "python_prompt": "Return the result of evaluating a given boolean expression, represented as a string.\nAn expression can either be:\n\n\"t\", evaluating to True;\n\"f\", evaluating to False;\n\"!(expr)\", evaluating to the logical NOT of the inner expression expr;\n\"&(expr1,expr2,...)\", evaluating to the logical AND of 2 or more inner expressions expr1, expr2, ...;\n\"|(expr1,expr2,...)\", evaluating to the logical OR of 2 or more inner expressions expr1, expr2, ...\n\n\xa0\nExample 1:\nInput: expression = \"!(f)\"\nOutput: true\n\nExample 2:\nInput: expression = \"|(f,t)\"\nOutput: true\n\nExample 3:\nInput: expression = \"&(t,f)\"\nOutput: false\n\nExample 4:\nInput: expression = \"|(&(t,f,t),!(t))\"\nOutput: false\n\n\xa0\nConstraints:\n\n1 <= expression.length <= 20000\nexpression[i]\xa0consists of characters in {\'(\', \')\', \'&\', \'|\', \'!\', \'t\', \'f\', \',\'}.\nexpression is a valid expression representing a boolean, as given in the description.",
        "python_signature": "",
        "python_code": "class Solution:\\n    def parseBoolExpr(self, expression: str) -> bool:\\n        if expression == \'f\':\\n            return False\\n        if expression == \'t\':\\n            return True\\n        if expression[0] == \'!\':\\n            return not self.parseBoolExpr(expression[2:-1])\\n        if expression[0] == \'|\':\\n            cursor = 2\\n            while cursor < len(expression)-1:\\n                end_of_next = self.getNextExpr(expression, cursor)\\n                if self.parseBoolExpr(expression[cursor:end_of_next]):\\n                    return True\\n                cursor = end_of_next + 1\\n            return False\\n        if expression[0] == \'&\':\\n            cursor = 2\\n            while cursor < len(expression)-1:\\n                end_of_next = self.getNextExpr(expression, cursor)\\n                if not self.parseBoolExpr(expression[cursor:end_of_next]):\\n                    return False\\n                cursor = end_of_next + 1\\n            return True\\n    \\n    def getNextExpr(self, expression, start):\\n        if expression[start] == \'!\' or expression[start] == \'|\' or expression[start] == \'&\':\\n            open_count = 1\\n            close_count = 0\\n            start += 1\\n            while open_count > close_count:\\n                start += 1\\n                if expression[start] == \'(\':\\n                    open_count += 1\\n                if expression[start] == \')\':\\n                    close_count += 1\\n                \\n            return start + 1\\n        else:\\n            return start + 1",
        "python_test": "\"inputs\": [[\"!(f)\"],[\"|(f,t)\"],[\"&(t,f)\"],[\"|(&(t,f,t),!(t))\"]], \"outputs\": [true,true,false,false]",
        "c_prompt": "",
        "c_signature": "bool parseBoolExpr(char *expression);",
        "c_code": "#include <string.h>\n#include <assert.h>\n#include <stdbool.h>\n\n// Function to evaluate a boolean expression\nbool parseBoolExpr(char *expression);\n\n// Helper function to get the next expression from a given position in the string\nint getNextExpr(char *expression, int start) {\n    if (expression[start] == '!' || expression[start] == '|' || expression[start] == '&') {\n        int open_count = 1;\n        int close_count = 0;\n        start++;\n\n        while (open_count > close_count) {\n            if (expression[start] == '(') {\n                open_count++;\n            }\n            if (expression[start] == ')') {\n                close_count++;\n            }\n            start++;\n        }\n    } else {\n        // Move one character ahead if it's not a nested expression\n        start++;\n    }\n    return start;\n}\n\n// Main function to parse and evaluate the boolean expression\nbool parseBoolExpr(char *expression) {\n    if (expression[0] == 'f') {\n        return false;\n    }\n    if (expression[0] == 't') {\n        return true;\n    }\n    if (expression[0] == '!') {\n        return !parseBoolExpr(expression + 2); // Skip \"!(\" and the final \")\"\n    }\n    if (expression[0] == '|') {\n        int cursor = 2;\n        while (cursor < strlen(expression) - 1) {\n            int end_of_next = getNextExpr(expression, cursor);\n            if (parseBoolExpr(strndup(expression + cursor, end_of_next - cursor))) {\n                return true;\n            }\n            cursor = end_of_next + 1;\n        }\n        return false;\n    }\n    if (expression[0] == '&') {\n        int cursor = 2;\n        while (cursor < strlen(expression) - 1) {\n            int end_of_next = getNextExpr(expression, cursor);\n            if (!parseBoolExpr(strndup(expression + cursor, end_of_next - cursor))) {\n                return false;\n            }\n            cursor = end_of_next + 1;\n        }\n        return true;\n    }\n    return false;  // Should not reach here for valid expressions\n}",
        "c_test": "void runTest(char *input, bool expected) {\n    bool result = parseBoolExpr(input);\n    assert(result == expected);\n}\n\nint main() {\n    // Test Cases\n    runTest(\"!(f)\", true);\n    runTest(\"|(f,t)\", true);\n    runTest(\"&(t,f)\", false);\n    runTest(\"|(&(t,f,t),!(t))\", false);\n\n    return 0;\n}"
    },
    {
        "python_prompt": "Find all possible combinations of k numbers that add up to a number n, given that only numbers from 1 to 9 can be used and each combination should be a unique set of numbers.\n\nNote:\n\n\n       All numbers will be positive integers.\n       The solution set must not contain duplicate combinations.\n\n\nExample 1:\n\n\nInput: k = 3, n = 7\nOutput: [[1,2,4]]\n\n\nExample 2:\n\n\nInput: k = 3, n = 9\nOutput: [[1,2,6], [1,3,5], [2,3,4]]",
        "python_signature": "",
        "python_code": "class Solution:\\n     def combinationSum3(self, k, n):\\n         \"\"\"\\n         :type k: int\\n         :type n: int\\n         :rtype: List[List[int]]\\n         \"\"\"\\n         to_return = []\\n         self.backtrack(to_return, [], k, n, 1)\\n         return to_return\\n     \\n     def backtrack(self, to_return, temp, k, n, start):\\n         total = sum(temp)\\n         \\n         if total > n:\\n             return\\n         if len(temp) == k and total == n:\\n             to_return.append(temp[:])\\n             return\\n         \\n         for i in range(start, 10):\\n             temp.append(i)\\n             self.backtrack(to_return, temp, k, n, i + 1)\\n             temp.pop()",
        "python_test": "\"inputs\": [[3,7], [3, 9], [9, 45]], \"outputs\": [[[1,2,4]], [[1,2,6],[1,3,5],[2,3,4]], [[1,2,3,4,5,6,7,8,9]]]",
        "c_prompt": "",
        "c_signature": "int** combinationSum3(int k, int n, int* returnSize);",
        "c_code": "#include <stdio.h>#include <stdlib.h>#include <assert.h>\\n\\nvoid backtrack(int** result, int* returnSize, int* temp, int tempSize, int k, int n, int start) {\\n    int total = 0;\\n    for (int i = 0; i < tempSize; i++) {\\n        total += temp[i];\\n    }\\n\\n    if (total > n) {\\n        return;\\n    }\\n    if (tempSize == k && total == n) {\\n        result[*returnSize] = (int*)malloc(k * sizeof(int));\\n        for (int i = 0; i < k; i++) {\\n            result[*returnSize][i] = temp[i];\\n        }\\n        (*returnSize)++;\\n        return;\\n    }\\n\\n    for (int i = start; i <= 9; i++) {\\n        temp[tempSize] = i;\\n        backtrack(result, returnSize, temp, tempSize + 1, k, n, i + 1);\\n    }\\n}\\n\\nint** combinationSum3(int k, int n, int* returnSize) {\\n    int maxCombinations = 100;  // This should be large enough to hold the result\\n    int** result = (int**)malloc(maxCombinations * sizeof(int*));\\n    int* temp = (int*)malloc(k * sizeof(int));\\n    *returnSize = 0;\\n    backtrack(result, returnSize, temp, 0, k, n, 1);\\n\\n    free(temp);\\n    return result;\\n}\\n",
        "c_test": "void free_result(int** result, int returnSize) { for (int i = 0; i < returnSize; i++) { free(result[i]); } free(result); } int main() { int returnSize1 = 0; int k1 = 3, n1 = 7; int** result1 = combinationSum3(k1, n1, &returnSize1); int expected1[1][3] = {{1, 2, 4}}; assert(returnSize1 == 1); for (int i = 0; i < returnSize1; i++) { for (int j = 0; j < 3; j++) { assert(result1[i][j] == expected1[i][j]); } } free_result(result1, returnSize1); int returnSize2 = 0; int k2 = 3, n2 = 9; int** result2 = combinationSum3(k2, n2, &returnSize2); int expected2[3][3] = {{1, 2, 6}, {1, 3, 5}, {2, 3, 4}}; assert(returnSize2 == 3); for (int i = 0; i < returnSize2; i++) { for (int j = 0; j < 3; j++) { assert(result2[i][j] == expected2[i][j]); } } free_result(result2, returnSize2); int returnSize3 = 0; int k3 = 9, n3 = 45; int** result3 = combinationSum3(k3, n3, &returnSize3); int expected3[1][9] = {{1, 2, 3, 4, 5, 6, 7, 8, 9}}; assert(returnSize3 == 1); for (int i = 0; i < returnSize3; i++) { for (int j = 0; j < 9; j++) { assert(result3[i][j] == expected3[i][j]); } } free_result(result3, returnSize3); printf(\"All test cases passed!\\n\"); return 0; }"
    },
    {
        "python_prompt": "Given a collection of distinct integers, return all possible permutations.\n\nExample:\n\n\nInput: [1,2,3]\nOutput:\n[\n  [1,2,3],\n  [1,3,2],\n  [2,1,3],\n  [2,3,1],\n  [3,1,2],\n  [3,2,1]\n]",
        "python_signature": "",
        "python_code": "class Solution:\\n     def permute(self, nums):\\n         \"\"\"\\n         :type nums: List[int]\\n         :rtype: List[List[int]]\\n         \"\"\"\\n         all_permutes = []\\n         self.permute_nums(all_permutes, nums, [])\\n         return all_permutes\\n     \\n     def permute_nums(self, all_permutes, nums, cur_permute):\\n         if len(nums) == 0:\\n             all_permutes.append(cur_permute)\\n             return\\n \\n         for i in range(len(nums)):\\n             num = nums[i]\\n \\n             self.permute_nums(all_permutes, nums[0:i] + nums[i+1:len(nums)], cur_permute + [num])",
        "python_test": "\"inputs\": [[[1,2,3]], [[0,1]], [[1]]], \"outputs\": [[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]], [[0,1],[1,0]], [[1]]]",
        "c_prompt": "",
        "c_signature": "int** permute(int* nums, int numsSize, int* returnSize);",
        "c_code": "#include <stdio.h>#include <stdlib.h>#include <assert.h>\n\nvoid permute_nums(int** result, int* returnSize, int* nums, int numsSize, int* currentPermute, int currentSize) {\n    if (currentSize == numsSize) {\n        // Copy current permutation to result\n        result[*returnSize] = (int*)malloc(numsSize * sizeof(int));\n        for (int i = 0; i < numsSize; i++) {\n            result[*returnSize][i] = currentPermute[i];\n        }\n        (*returnSize)++;\n        return;\n    }\n\n    for (int i = 0; i < numsSize; i++) {\n        int found = 0;\n        // Check if nums[i] is already in currentPermute\n        for (int j = 0; j < currentSize; j++) {\n            if (currentPermute[j] == nums[i]) {\n                found = 1;\n                break;\n            }\n        }\n        if (found) continue;\n\n        currentPermute[currentSize] = nums[i];\n        permute_nums(result, returnSize, nums, numsSize, currentPermute, currentSize + 1);\n    }\n}\n\nint** permute(int* nums, int numsSize, int* returnSize) {\n    int maxPermutes = 1;\n    for (int i = 1; i <= numsSize; i++) {\n        maxPermutes *= i;\n    }\n    int** result = (int**)malloc(maxPermutes * sizeof(int*));\n    int* currentPermute = (int*)malloc(numsSize * sizeof(int));\n    *returnSize = 0;\n    permute_nums(result, returnSize, nums, numsSize, currentPermute, 0);\n    free(currentPermute);\n    return result;\n}\n",
        "c_test": "void free_result(int** result, int returnSize) {\n    for (int i = 0; i < returnSize; i++) {\n        free(result[i]);\n    }\n    free(result);\n}\n\nint main() {\n    // Test Case 1\n    int nums1[] = {1, 2, 3};\n    int returnSize1 = 0;\n    int** result1 = permute(nums1, 3, &returnSize1);\n    int expected1[6][3] = {{1, 2, 3}, {1, 3, 2}, {2, 1, 3}, {2, 3, 1}, {3, 1, 2}, {3, 2, 1}};\n    assert(returnSize1 == 6);\n    for (int i = 0; i < returnSize1; i++) {\n        for (int j = 0; j < 3; j++) {\n            assert(result1[i][j] == expected1[i][j]);\n        }\n    }\n    free_result(result1, returnSize1);\n\n    // Test Case 2\n    int nums2[] = {0, 1};\n    int returnSize2 = 0;\n    int** result2 = permute(nums2, 2, &returnSize2);\n    int expected2[2][2] = {{0, 1}, {1, 0}};\n    assert(returnSize2 == 2);\n    for (int i = 0; i < returnSize2; i++) {\n        for (int j = 0; j < 2; j++) {\n            assert(result2[i][j] == expected2[i][j]);\n        }\n    }\n    free_result(result2, returnSize2);\n\n    // Test Case 3\n    int nums3[] = {1};\n    int returnSize3 = 0;\n    int** result3 = permute(nums3, 1, &returnSize3);\n    int expected3[1][1] = {{1}};\n    assert(returnSize3 == 1);\n    for (int i = 0; i < returnSize3; i++) {\n        for (int j = 0; j < 1; j++) {\n            assert(result3[i][j] == expected3[i][j]);\n        }\n    }\n    free_result(result3, returnSize3);\n\n    printf(\"All test cases passed!\\n\");\n\n    return 0;\n}"
    }
]

translate_lcb_call_based_shots = [
    {
        "python_prompt": "Rotates a 2D matrix 90 degrees clockwise in-place.\nArgs:\nmatrix: A square 2D list of integers\nReturns:\nThe rotated matrix (original matrix is modified in-place)\nExample:\n>>> matrix = [[1,2,3],[4,5,6],[7,8,9]]\n>>> rotate_matrix(matrix)\n[[7,4,1],[8,5,2],[9,6,3]]",
        "python_signature": "def rotate_matrix(matrix: List[List[int]]) -> List[List[int]]:",
        "test": {
            "input": [[1,2,3],[4,5,6],[7,8,9]],
            "output": [[7,4,1],[8,5,2],[9,6,3]]
        },
        "c_signature": "long long** rotateMatrix(long long** matrix, int n);",
        "c_code":
        """
          #include <stdlib.h>

long long** rotateMatrix(long long** matrix, int n) {
    long long** result = (long long**)malloc(n * sizeof(long long*));
    for (int i = 0; i < n; i++) {
        result[i] = (long long*)malloc(n * sizeof(long long));
        for (int j = 0; j < n; j++) {
            result[i][j] = matrix[n - j - 1][i];
        }
    }
    return result;
}
        """,
        "c_config": {
            "args": ["long long**", "int"],
    "return": {
        "type": "array",
        "element_type": "long long",
        "dimension": 2
    }
        },
    },
    {
      "python_prompt": "Implement a function to count the number of passengers strictly older than 60 years based on encoded passenger details",
      "python_signature": "def count_seniors(details: List[str]) -> int:",
      "test": {
        "input": ["7868190130M7522", "5303914400F9211", "9273338290F4010"],
        "output": 2
      },
      "c_signature": "int countSeniors(char** details, int detailsSize);",
      "c_code": """
        #include <stdlib.h>
        #include <string.h>
        
        int countSeniors(char** details, int detailsSize) {
            int count = 0;
            for (int i = 0; i < detailsSize; i++) {
                // Extract age (characters 11-12, 0-based index)
                char ageStr[3] = {details[i][11], details[i][12], '\\0'};
                int age = atoi(ageStr);
                if (age > 60) count++;
            }
            return count;
        }
        """,
      "c_config": {
          "args": ["char**", "int"],
          "return": {
            "type": "int"
          }
      }
    },
    {
        "python_prompt": "You are given a 0-indexed 2D integer array nums. Initially, your score is 0. Perform the following operations until the matrix becomes empty:\n\nFrom each row in the matrix, select the largest number and remove it. In the case of a tie, it does not matter which number is chosen.\nIdentify the highest number amongst all those removed in step 1. Add that number to your score.\n\nReturn the final score.",
        "python_signature": "def matrixScore(nums: List[List[int]]) -> int:",
        "test": {
            "input": [[7, 2, 1], [6, 4, 2], [6, 5, 3], [3, 2, 1]],
            "output": 15
        },
        "c_signature": "long long matrixScore(long long** nums, int numsSize, int numsColSize);",
        "c_code":
            """
           #include <stdlib.h>

int compare_desc(const void* a, const void* b) {
    long long val_a = *(long long*)a;
    long long val_b = *(long long*)b;
    return (val_b > val_a) - (val_b < val_a); // 避免 overflow
}

long long matrixScore(long long** nums, int numsSize, int numsColSize) {
    long long total_score = 0;

    // 每一行排序（从大到小）
    for (int i = 0; i < numsSize; i++) {
        qsort(nums[i], numsColSize, sizeof(long long), compare_desc);
    }

    for (int col = 0; col < numsColSize; col++) {
        long long max_in_col = 0;
        for (int row = 0; row < numsSize; row++) {
            if (nums[row][col] > max_in_col) {
                max_in_col = nums[row][col];
            }
        }
        total_score += max_in_col;
    }

    return total_score;
}
            """,
        "c_config": {
            "args": ["long long**", "int", "int"],
            "return": {
            "type": "long long",
            "element_type": ""
            }
        }
    },
    {
        "python_prompt": "Determine whether a binary array exists that could produce the given derived array using XOR rules as specified.",
        "python_signature": "def does_valid_array_exist(derived: List[int]) -> bool:",
        "test": {
            "input": [1, 1, 0],
            "output": True
        },
        "c_signature": "bool doesValidArrayExist(long long* derived, int derivedSize);",
        "c_code": """
    #include <stdbool.h>

bool doesValidArrayExist(long long* derived, int derivedSize) {
    long long xor_sum = 0;
    for (int i = 0; i < derivedSize; i++) {
        xor_sum ^= derived[i];
    }
    return xor_sum == 0;
}
      """,
        "c_config": {
             "args": ["long long*", "int"],
    "return": {
        "type": "bool"
    }
        }
    },
 {
        "python_prompt": "You are given an array arr of size n consisting of non-empty strings.\nFind a string array answer of size n such that:\n\nanswer[i] is the shortest substring of arr[i] that does not occur as a substring in any other string in arr.",
        "python_signature": "class Solution:\n    def shortestSubstrings(self, arr: List[str]) -> List[str]:",
        "test": {
            "input": [["cab", "ad", "bad", "c"]],
            "output": ["ab", "", "ba", ""]
        },
        "c_signature": "char** findShortestUniqueSubstrings(char** arr, int arrSize);",
        "c_code": """
   #include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdio.h>
#include <math.h>

// Function to check if a substring exists in any other string
bool existsInOtherStrings(char* sub, char** arr, int arrSize, int index) {
    for (int i = 0; i < arrSize; i++) {
        if (i != index && strstr(arr[i], sub) != NULL) {
            return true;
        }
    }
    return false;
}

// Function to compare two strings lexicographically
int compareStrings(const void* a, const void* b) {
    return strcmp((const char*)a, (const char*)b);
}

char** findShortestUniqueSubstrings(char** arr, int arrSize) {
    char** answer = (char**)malloc(arrSize * sizeof(char*));
    for (int i = 0; i < arrSize; i++) {
        int len = strlen(arr[i]);
        bool found = false;
        for (int subLen = 1; subLen <= len &&!found; subLen++) {
            char** substrings = (char**)malloc(len * sizeof(char*));
            int subCount = 0;
            for (int start = 0; start <= len - subLen; start++) {
                substrings[subCount] = (char*)malloc((subLen + 1) * sizeof(char));
                strncpy(substrings[subCount], arr[i] + start, subLen);
                substrings[subCount][subLen] = '\0';
                subCount++;
            }
            qsort(substrings, subCount, sizeof(char*), compareStrings);
            for (int j = 0; j < subCount &&!found; j++) {
                if (!existsInOtherStrings(substrings[j], arr, arrSize, i)) {
                    answer[i] = (char*)malloc((subLen + 1) * sizeof(char));
                    strcpy(answer[i], substrings[j]);
                    found = true;
                }
                free(substrings[j]);
            }
            free(substrings);
        }
        if (!found) {
            answer[i] = (char*)malloc(1 * sizeof(char));
            answer[i][0] = '\0';
        }
    }
    return answer;
}
      """,
        "c_config": {
             "args": ["char**", "int"],
        'return': {'type': 'array','element_type': 'char', 'dimension': 2}
        }
    },
{
        "python_prompt": "Given three strings a, b, and c, your task is to find a string that has the minimum length and contains all three strings as substrings.",
        "python_signature": "class Solution:\n    def minimumString(self, a: str, b: str, c: str) -> str:",
        "test": {
            "input": ["abc", "bca", "aaa"],
            "output": "aaabca",
        },
        "c_signature": "bool doesValidArrayExist(long long* derived, int derivedSize);",
        "c_code": """
    #include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

bool containsSubstring(const char *mainStr, const char *subStr) {
    return strstr(mainStr, subStr) != NULL;
}

// 拼接两个字符串，若已重叠部分尽可能共享
char *mergeStrings(const char *s1, const char *s2) {
    long long len1 = strlen(s1);
    long long len2 = strlen(s2);
    long long maxOverlap = (len1 < len2) ? len1 : len2;

    for (long long overlap = maxOverlap; overlap > 0; overlap--) {
        if (strncmp(s1 + len1 - overlap, s2, overlap) == 0) {
            long long totalLen = len1 + len2 - overlap;
            char *merged = (char *)malloc((totalLen + 1) * sizeof(char));
            strcpy(merged, s1);
            strcpy(merged + len1, s2 + overlap);
            return merged;
        }
    }
    // 没有重叠，简单连接
    long long totalLen = len1 + len2;
    char *merged = (char *)malloc((totalLen + 1) * sizeof(char));
    strcpy(merged, s1);
    strcpy(merged + len1, s2);
    return merged;
}

// 检查字符串是否是同时包含 a、b、c 的超级字符串
bool isValid(const char *str, const char *a, const char *b, const char *c) {
    return containsSubstring(str, a) && containsSubstring(str, b) && containsSubstring(str, c);
}

// 比较结果是否更优：长度更小，若长度相同，按字典序更小。
bool isBetterResult(const char *newResult, const char *bestResult) {
    long long newLen = strlen(newResult);
    long long bestLen = strlen(bestResult);
    if (newLen < bestLen) return true;
    if (newLen == bestLen && strcmp(newResult, bestResult) < 0) return true;
    return false;
}

char *findSmallestContainingString(char *a, char *b, char *c) {
    const char *arr[3] = {a, b, c};
    int perms[6][3] = {
        {0,1,2},
        {0,2,1},
        {1,0,2},
        {1,2,0},
        {2,0,1},
        {2,1,0}
    };
    long long bestLen = strlen(a) + strlen(b) + strlen(c) + 1;
    char *bestResult = (char *)malloc(bestLen);
    bestResult[0] = '\0';

    for (int i = 0; i < 6; i++) {
        const char *s1 = arr[perms[i][0]];
        const char *s2 = arr[perms[i][1]];
        const char *s3 = arr[perms[i][2]];

        char *merged12 = mergeStrings(s1, s2);
        char *mergedFinal = mergeStrings(merged12, s3);

        if (isValid(mergedFinal, a, b, c) && 
            (strlen(bestResult) == 0 || isBetterResult(mergedFinal, bestResult))) {
            strcpy(bestResult, mergedFinal);
        }

        free(merged12);
        free(mergedFinal);
    }

    // 重新分配最终结果，避免过大空间浪费
    long long finalLen = strlen(bestResult);
    char *finalResult = (char *)malloc((finalLen + 1) * sizeof(char));
    strcpy(finalResult, bestResult);
    free(bestResult);
    return finalResult;
}
      """,
        "c_config": {
            'args': ['char*', 'char*', 'char*'], 'return': {'type': 'array', 'element_type': 'char', 'dimension': 1}
        }
    }
]
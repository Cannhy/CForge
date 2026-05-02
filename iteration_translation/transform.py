import datasets
import json

from process_human_eval import write_jsonl, read_problems


# ['problem_id', 'question', 'solutions', 'input_output', 'difficulty', 'url', 'starter_code']
dataset =datasets.load_from_disk("apps/dataset")
for ds in dataset:
    if ds['problem_id'] == 3246:
        print("---question---")
        print(ds['question'])
        print("---solutions---")
        print(ds['solutions'])


        print("---input_output---")
        # print(ds['input_output'])

        parsed_data = json.loads(ds['input_output'])
        paired = [{"input": inp, "output": out} for inp, out in zip(parsed_data["inputs"], parsed_data["outputs"])]
        print(paired)

        print("---starter_code---")
        print(ds['starter_code'])
        i = 0
# for data_point in dataset:
#     i += 1
#     if 201 <= i <= 1000:
#         write_jsonl("apps/apps_python.jsonl", [data_point], append=True)
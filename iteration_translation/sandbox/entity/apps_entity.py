
class AppsEntity:
    def __init__(self, problem_id: int, prompt: str, signature: str, code: str, test_code: str, input_output: str):
        self.id = problem_id
        self.signature = signature
        self.prompt = prompt
        self.code = code
        self.test_code = test_code
        self.input_output = input_output

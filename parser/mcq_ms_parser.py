from parser.ms_parser import Parser
from typing import List, Optional
from parser.models.question import MultipleChoiceQuestion


class MCQMSParser(Parser):
    def __init__(
        self,
        pdf_path: str,
        mcqs: List[MultipleChoiceQuestion],
        image_prefix: str = "images/example-",
    ):
        self.mcqs = mcqs
        super().__init__(pdf_path, image_prefix)

    def parse_no_error(self):
        # parse if there is no parse error in ms and qp
        for question, answer in zip(self.mcqs, self.tables[1:]):
            if question.number != int(answer["Question"]):
                print(
                    f"Question number mismatch: {question.number} != {answer['Question']}, switching to parse_with_error"
                )
                return self.parse_with_error()
            question.answer = answer["Answer"]
            question.marks = int(answer["Marks"])
            question.ms_image = answer["Image"]
        return True

    def parse_with_error(self):
        # parse if there is parse error in ms and qp
        # sort questions and answers by number for easier matching
        self.mcqs.sort(key=lambda x: x.number)
        answers = sorted(self.tables[1:], key=lambda x: int(x["Question"]))

        # Initialize two pointers
        q_ptr = 0  # pointer for questions
        a_ptr = 0  # pointer for answers

        while q_ptr < len(self.mcqs) and a_ptr < len(answers):
            q_num = self.mcqs[q_ptr].number
            a_num = int(answers[a_ptr]["Question"])

            if q_num == a_num:
                # Numbers match - assign answer and marks
                self.mcqs[q_ptr].answer = answers[a_ptr]["Answer"]
                self.mcqs[q_ptr].marks = int(answers[a_ptr]["Marks"])
                self.mcqs[q_ptr].ms_image = answers[a_ptr]["Image"]
                q_ptr += 1
                a_ptr += 1
            elif q_num < a_num:
                # Question number is smaller, skip question
                q_ptr += 1
                print(
                    f"Skipping question {q_num} as it has no answer in the mark scheme."
                )
            else:
                # Answer number is smaller, skip answer
                a_ptr += 1
                print(f"Skipping answer {a_num} as it has no corresponding question.")

        return q_ptr > 0 and a_ptr > 0


if __name__ == "__main__":
    from models.question import MultipleChoiceQuestion

    # Example usage
    pdf_path = "papers/igcse-biology-0610/0610_w22_ms_12.pdf"
    mcqs = [
        MultipleChoiceQuestion(number=i, text=f"Question {i}", options=[])
        for i in range(1, 41, 2)
    ]
    parser = MCQMSParser(pdf_path, mcqs)
    parser.parse_no_error()
    for mcq in parser.mcqs:
        if mcq.answer is not None:
            print(mcq.number, mcq.text, mcq.answer, mcq.marks)

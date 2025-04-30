import textwrap
import re

def generate_answer_variants(ans):
    if ans.lower() in ['t', 'true', 'f', 'false']:
        return ["T", "t", "True", "true"] if ans.lower().startswith('t') else ["F", "f", "False", "false"]
    else:
        return [ans.upper(), ans.lower()]

def strip_parentheses(text):
    return re.sub(r"\s*\(.*?\)", "", text).strip()

def wrap_line(line):
    return textwrap.wrap(line, width=68)

def format_question_block(question, options, answer):
    lines = textwrap.wrap(question.strip(), width=68)
    formatted = lines[:1]  # Question title line
    formatted += [f"     {opt}" for opt in options]
    while len(formatted) < 6:
        formatted.append("")  # Pad to 6
    formatted.append("")  # 7th line
    return f'    ("""' + "\n".join(formatted) + '""",\n     ' + str(generate_answer_variants(answer)) + '),\n'

def parse_blocks(raw_lines):
    blocks = []
    current_q = ""
    options = []
    answer = ""
    for line in raw_lines:
        line = line.strip()
        if line.lower().startswith("answer:"):
            answer = line.split(":")[1].strip()
            blocks.append((current_q.strip(), options[:], answer))
            current_q, options, answer = "", [], ""
        elif re.match(r"^[A-Da-d]\)", line):
            options.append(strip_parentheses(line))
        elif line.startswith("- True") or line.startswith("- False"):
            options = ["- True", "- False"]
            current_q += "\n" + line  # Add this line as part of the question
        elif line:
            current_q += (" " + line if current_q else line)
    return blocks

def main():
    print("Paste your raw input below. Type 'END' on a new line when done:")
    raw_lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        raw_lines.append(line)

    qa_blocks = parse_blocks(raw_lines)
    print("\nFormatted Output:\n")
    print("tasks = [")
    for question, options, answer in qa_blocks:
        print(format_question_block(question, options, answer))
    print("]")
    print("Done!")

if __name__ == "__main__":
    main()

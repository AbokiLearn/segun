from pathlib import Path
import tiktoken

data_path = Path("/home/muaddib/arrakis/AbokiLearn/aboki-segun/data")
tokenizer = tiktoken.encoding_for_model("gpt-4o")


def main():
    csv = '"path","tokens"\n'

    for folder in data_path.glob("*"):
        for file in folder.glob("*"):
            with open(file, "r") as f:
                text = f.read()
            tokens = tokenizer.encode(text)
            csv += f'"{file}",{len(tokens)}\n'

    with open(data_path / "token_counts.csv", "w") as f:
        f.write(csv)


if __name__ == "__main__":
    main()

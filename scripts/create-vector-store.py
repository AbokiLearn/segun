"""create-vector-store

This script will retrieve files from [this](https://huggingface.co/datasets/Kabilan108/js-docs)
and will upload them to a new vector-store via the OpenAI Assistants API.
"""

from datasets import load_dataset
from openai import OpenAI

client = OpenAI()


def main():
    ds = load_dataset("Kabilan108/js-docs")
    files = ds["train"]["files"]
    del ds

    file_streams = [
        (file["filename"], file["content"].encode("utf-8")) for file in files
    ]

    vector_store = client.beta.vector_stores.create(name="wazobiacode-docs-dev")
    print(f"Created vector store {vector_store.id}")

    for i in range(0, len(file_streams), 500):
        batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams[i : i + 500],
        )
        print(f"Uploaded batch {i // 500 + 1}")
        print(f"\tstatus: {batch.status}\n\tcount: {batch.file_counts}")


if __name__ == "__main__":
    main()

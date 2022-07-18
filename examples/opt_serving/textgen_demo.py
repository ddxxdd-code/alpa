"""Use huggingface/transformers interface and Alpa backend for distributed inference."""
from transformers import AutoTokenizer
from opt_serving.model.wrapper import get_model
import numpy as np

# Load the tokenizer. We have to use the 30B version because
# other versions have some issues. The 30B version works for all OPT models.
tokenizer = AutoTokenizer.from_pretrained("facebook/opt-30b", use_fast=False)
tokenizer.add_bos_token = False

generate_params = {"do_sample": False, "num_beams": 1, "num_return_sequences": 1}

# Load the model
model = get_model(model_name="alpa/opt-30b",
                  device="cuda",
                  path="/home/ubuntu/opt_weights",
                  batch_size=4,
                  **generate_params)

# Generate
prompt = [
    "Paris is the capital city of",
          "Today is a good day and I'd like to",
          "Computer Science studies the area of",
          "University of California Berkeley is a public university"]
# prompt = "Paris is the capital city of"
input_ids = tokenizer(prompt, return_tensors="pt", padding="longest").input_ids.to("cuda")
print(input_ids)

input_ids_np = input_ids.cpu().numpy()
pad_value = 1
attention_mask = ((input_ids_np == pad_value) * -1e10) [:, None, None, :]
# np.pad(attention_mask, )
new_attention_mask = np.zeros([input_ids_np.shape[0], 1, 1, 2048], dtype=np.float16)
new_attention_mask[:, :, :, :attention_mask.shape[-1]] = attention_mask

print(new_attention_mask[:,:,:,:8])

outputs = model.generate(input_ids=input_ids,
                         max_length=32,
                         alpa_attention_mask=new_attention_mask,
                         **generate_params)

# Print results
print("Output:\n" + 100 * '-')
for i, output in enumerate(outputs):
    print("{}: {}".format(i, tokenizer.decode(output,
                                              skip_special_tokens=True)))
    print(100 * '-')

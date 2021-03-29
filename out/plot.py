import matplotlib.pyplot as plt
import pandas as pd

eval_all = pd.read_csv('all/time.csv')
print(eval_all)
eval_linear = pd.read_csv('linear/time.csv')
print(eval_linear)

# plot All
plt.plot(eval_all['N'], eval_all['time'], marker='o', markersize=5, color="blue", label="all-to-all")
# plot Linear
plt.plot(eval_linear['N'], eval_linear['time'], marker='o', markersize=5, color="red", label="linear")

plt.title("Querying Peers Evaluation")
plt.xlabel("Number of Querying Peers")
plt.ylabel("Total Response time(sec)")

plt.legend()

plt.savefig("eval.png")
plt.show()
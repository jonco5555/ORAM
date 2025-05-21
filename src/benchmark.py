import time

import matplotlib.pyplot as plt

from src.client import Client
from src.server import Server


def benchmark_throughput_vs_db_size(db_sizes):
    throughputs = []
    latencies = []
    for num_blocks in db_sizes:
        server = Server(num_blocks=num_blocks)
        client = Client(num_blocks=num_blocks)
        client._initialize_server_tree(server)

        repeats = 1000 // num_blocks

        start = time.time()
        for _ in range(repeats):
            for i in range(num_blocks):
                client.store_data(server, i, f"data_{i}")
                client.retrieve_data(server, i)

            for i in range(num_blocks):
                client.retrieve_data(server, i)
                client.delete_data(server, i)
        end = time.time()

        delta = end - start
        total_requests = repeats * 4 * num_blocks
        throughput = total_requests / delta
        latency = delta / total_requests
        throughputs.append(throughput)
        latencies.append(latency)
        print(f"{delta=}")
        print(f"N={num_blocks}: {throughput:.2f} req/sec")

    return throughputs, latencies


if __name__ == "__main__":
    db_sizes = [10, 50, 100, 200, 500, 1000]
    throughputs, latencies = benchmark_throughput_vs_db_size(db_sizes)
    plt.figure()
    plt.plot(db_sizes, throughputs, marker="o")
    plt.xlabel("N (DB size)")
    plt.ylabel("Throughput (requests/sec)")
    plt.title("Throughput vs. DB Size")
    plt.grid(True)
    plt.show()

    plt.figure()
    plt.plot(throughputs, [latency * 1000 for latency in latencies], marker="o")
    plt.xlabel("Throughput (requests/sec)")
    plt.ylabel("Latency (ms/request)")
    plt.title("Latency vs. Throughput")
    plt.grid(True)
    plt.show()

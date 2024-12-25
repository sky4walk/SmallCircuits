import torch
import time

print("CUDA verfügbar:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("CUDA-Version:", torch.version.cuda)
    print("GPU-Name:", torch.cuda.get_device_name(0))
else:
    print("Keine GPU gefunden oder CUDA nicht verfügbar.")

x = torch.tensor([1.0, 2.0, 3.0])
print("Tensor auf der CPU:", x)
print("Summe:", x.sum())

if torch.cuda.is_available():
    x = x.to("cuda")
    print("Tensor auf der GPU:", x)
    print("Summe (GPU):", x.sum())

# CPU-Berechnung
x_cpu = torch.rand((10000, 10000))
start_time = time.time()
_ = x_cpu @ x_cpu
print("CPU-Zeit:", time.time() - start_time)

# GPU-Berechnung (falls verfügbar)
if torch.cuda.is_available():
    x_gpu = x_cpu.to("cuda")
    start_time = time.time()
    _ = x_gpu @ x_gpu
    print("GPU-Zeit:", time.time() - start_time)
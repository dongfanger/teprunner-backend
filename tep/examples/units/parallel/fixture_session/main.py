import os.path

"""
测试时先运行main.py，然后在case100目录下执行pytest -n auto
"""

dir_name = "case20"

if not os.path.exists(dir_name):
    os.mkdir(dir_name)

for i in range(20):
    suffix = i + 1
    name = "test_" + str(suffix).zfill(3)
    with open(os.path.join(dir_name, name + ".py"), "w") as f:
        content = f"""import time


def test_{suffix}(lock):
    time.sleep(0.5)
"""
        f.write(content)

import os.path
import shutil

carry_path = os.path.dirname(os.path.abspath(__file__))
flow_path = os.path.join(os.path.dirname(carry_path), "test_login_to_pay_flow.py")
flow_data_path = os.path.join(os.path.dirname(carry_path), "test_login_to_pay_flow.json")
cases_path = os.path.join(carry_path, "cases")
if not os.path.exists(cases_path):
    os.mkdir(cases_path)

for i in range(100):
    print(i)
    shutil.copy2(flow_path, os.path.join(cases_path, f"test_login_to_pay_flow{str(i).zfill(4)}.py"))
    shutil.copy2(flow_data_path, os.path.join(cases_path, f"test_login_to_pay_flow{str(i).zfill(4)}.json"))

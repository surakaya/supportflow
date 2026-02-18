import pandas as pd
import random

billing_msgs = [
    "My payment failed",
    "Refund not received",
    "Invoice is wrong",
    "Charged twice",
    "Subscription issue",
    "Upgrade plan problem"
]

technical_msgs = [
    "Website is slow",
    "App crashes",
    "Bug in dashboard",
    "Login page error",
    "API not responding",
    "System timeout"
]

account_msgs = [
    "Can't login",
    "Reset password not working",
    "Change email address",
    "Account locked",
    "Two factor not working"
]

data = []

for _ in range(1000):
    category = random.choice(["billing", "technical", "account"])

    if category == "billing":
        message = random.choice(billing_msgs)
    elif category == "technical":
        message = random.choice(technical_msgs)
    else:
        message = random.choice(account_msgs)

    urgency = random.choices(
        ["low", "medium", "high"],
        weights=[0.3, 0.4, 0.3]
    )[0]

    # küçük noise ekle
    if random.random() < 0.3:
        message += " please help"
    if random.random() < 0.2:
        message += " urgently"

    data.append((message, category, urgency))

df = pd.DataFrame(data, columns=["message", "category", "urgency"])
df.to_csv("ml/training/tickets.csv", index=False)

print("Gerçekçi dataset oluşturuldu.")

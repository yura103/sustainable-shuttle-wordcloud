import pandas as pd
from kafka import KafkaProducer
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

producer = KafkaProducer(
    bootstrap_servers=[os.getenv('KAFKA_SERVER')],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

df = pd.read_csv('shuttle_final_data.csv')

print("🚀 실시간 데이터 전송 시작...")
for _, row in df.iterrows():
    # NaN(비어있는 값)을 None으로 변경 (Elasticsearch가 null로 인식할 수 있게)
    data = row.where(pd.notnull(row), None).to_dict()
    
    producer.send('shuttle-topic', data)
    print(f"🚀 전송 중: 학번 {data['학번']}")
    time.sleep(0.5)
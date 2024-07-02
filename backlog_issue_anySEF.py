import requests
import csv

# APIのベースURLとプロジェクトIDを設定します
base_url = 'https://yourdomain.backlog.com/api/v2'
project_id = 'your_project_id'

# APIキーを設定します
api_key = 'your_api_key'

# Issueを取得するエンドポイントURLを作成します
issue_endpoint = f'{base_url}/issues'

# リクエストヘッダーにAPIキーを含めます
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}

# 全てのIssueを取得するためのパラメータを設定します
params = {
    'projectId[]': project_id,
    'count': 100  # 必要に応じて変更
}

# カスタムフィールドIDを設定します
custom_field_id = 3

# SEFとtarget_value_idの対応を定義します
sef_to_value_ids = {
    '23A': [1, 2],
    '24A': [3, 4]
}

# フィルタリングされたIssueをSEF毎に格納する辞書を用意します
sef_issues = {sef: [] for sef in sef_to_value_ids.keys()}

# APIにGETリクエストを送信して全てのIssueを取得します
response = requests.get(issue_endpoint, headers=headers, params=params)

# レスポンスをJSON形式で取得します
if response.status_code == 200:
    issues = response.json()
    
    # 各Issueをチェック
    for issue in issues:
        for custom_field in issue.get('customFields', []):
            if custom_field['id'] == custom_field_id:
                for value in custom_field['value']:
                    # target_value_idとSEFの対応をチェックしてIssueを分類
                    for sef, value_ids in sef_to_value_ids.items():
                        if value['id'] in value_ids:
                            sef_issues[sef].append(issue)
                            break  # 一致する値が見つかったらループを抜ける

    # SEF毎にフィルタリングされたIssueをCSVファイルに保存
    for sef, issues in sef_issues.items():
        filename = f'{sef}_issues.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['issueKey', 'summary', 'description', 'status', 'assignee', 'created', 'updated']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for issue in issues:
                writer.writerow({
                    'issueKey': issue['issueKey'],
                    'summary': issue['summary'],
                    'description': issue.get('description', ''),
                    'status': issue['status']['name'],
                    'assignee': issue.get('assignee', {}).get('name', ''),
                    'created': issue['created'],
                    'updated': issue['updated']
                })
                
        print(f"SEF: {sef} - Issues saved to {filename}")
else:
    print(f"Failed to retrieve issues: {response.status_code} - {response.text}")

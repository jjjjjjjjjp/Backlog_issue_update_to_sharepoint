import requests
import pandas as pd
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

# Backlog APIの設定
BACKLOG_API_URL = "https://your_backlog_space.backlog.com/api/v2/issues"
BACKLOG_API_KEY = "your_backlog_api_key"

# SharePointの設定
SHAREPOINT_SITE_URL = "https://your_sharepoint_site_url"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

# プロジェクトIDごとに異なるカスタムフィールドを設定
PROJECT_CUSTOM_FIELDS = {
    123: [{"customField_1": 789, "customField_2": 1011}],  # プロジェクトID 123のカスタムフィールド
    456: [{"customField_3": 1112, "customField_4": 1314}],  # プロジェクトID 456のカスタムフィールド
    # 追加のプロジェクトとカスタムフィールドの組み合わせをここに追加
}

# プロジェクトとカスタムフィールドの組み合わせに対するファイルとシートの紐づけを設定
PROJECT_FILE_SHEET_MAPPING = {
    123: {
        (789, 1011): {
            "file": "/sites/your_site/Shared Documents/your_excel_file1.xlsx",
            "sheet": "Sheet1"
        }
    },
    456: {
        (1112, 1314): {
            "file": "/sites/your_site/Shared Documents/your_excel_file2.xlsx",
            "sheet": "Sheet2"
        }
    }
    # 追加のプロジェクトとカスタムフィールドの組み合わせをここに追加
}

# Backlogの課題一覧を取得する関数
def get_backlog_issues(param_json):
    params = {
        "apiKey": BACKLOG_API_KEY,
        **param_json  # 追加のパラメータをここで展開
    }
    response = requests.get(BACKLOG_API_URL, params=params)
    response.raise_for_status()
    return response.json()

# SharePointのExcelファイルを更新する関数
def update_sharepoint_excel(issues, xlsx_file, xlsx_sheet, sort_column):
    # 課題データをDataFrameに変換
    df = pd.DataFrame(issues)

    # SharePointの認証情報
    credentials = ClientCredential(CLIENT_ID, CLIENT_SECRET)
    ctx = ClientContext(SHAREPOINT_SITE_URL).with_credentials(credentials)

    # Excelファイルを取得
    response = File.open_binary(ctx, xlsx_file)

    # 既存のExcelファイルを読み込み
    with open("temp.xlsx", "wb") as f:
        f.write(response.content)
    df_existing = pd.read_excel("temp.xlsx", sheet_name=xlsx_sheet)

    # 新しいデータで上書き
    df_existing.update(df)

    # ソートする
    df_existing.sort_values(by=sort_column, inplace=True)

    # Excelファイルに書き込み
    with pd.ExcelWriter("temp.xlsx", engine='openpyxl', mode='w') as writer:  # 'w'モードに変更
        df_existing.to_excel(writer, sheet_name=xlsx_sheet, index=False)

    # 更新したExcelファイルをSharePointにアップロード
    with open("temp.xlsx", "rb") as f:
        target_file = ctx.web.get_file_by_server_relative_url(xlsx_file)
        target_file.upload(f.read())
        ctx.execute_query()

# メイン処理
if __name__ == "__main__":
    for project_id, custom_fields_list in PROJECT_CUSTOM_FIELDS.items():
        for custom_fields in custom_fields_list:
            # BacklogのAPIに渡すパラメータを指定
            param_json = {
                "projectId[]": project_id,  # プロジェクトIDを指定
                **custom_fields  # カスタムフィールドの値を指定
            }

            # Backlogの課題一覧を取得
            issues = get_backlog_issues(param_json)

            # カスタムフィールドの値のタプルを生成
            custom_field_values = tuple(custom_fields.values())

            # ファイルとシートの情報を取得
            file_sheet_info = PROJECT_FILE_SHEET_MAPPING[project_id][custom_field_values]
            xlsx_file = file_sheet_info["file"]
            xlsx_sheet = file_sheet_info["sheet"]

            # SharePointのExcelファイルを更新
            update_sharepoint_excel(issues, xlsx_file, xlsx_sheet, "column_to_sort_by")

## 使用步驟
在"輸入專案名稱"的地方輸入你的專案名稱。
點擊"建立虛擬環境"。

## For Developer

### 建立虛擬環境

1. 安裝 `virtualenv`：
    ```bat
    pip install virtualenv
    ```

2. 建立虛擬環境：
    ```bat
    virtualenv myenv
    ```

3. 啟動虛擬環境：
    - Windows:
        ```bat
        .\myenv\Scripts\activate
        ```
    - macOS/Linux:
        ```bat
        source myenv/bin/activate
        ```

### 安裝套件

在虛擬環境啟動後，執行：
```bat
pip install -r requirements.txt
```

### 如果要編譯成exe檔

```bat
pip install pyinstaller
```

```bat
pyinstaller setup_venv.spec
```
# 政大水火研究團隊新聞爬蟲

## 環境設定
建立運行的虛擬環境
```
pipenv --python 3.6
```

安裝需要的套件
```
pipenv install
```

## 安裝 mysqlclient
1. 安裝 gcc 編譯環境
因為 mysqlclient 底層是使用 c 語言撰寫，所以需要 c 的編譯環境
```bash
sudo apt install build-essential
```

2. 安裝 python3-dev
```bash
sudo apt install python3-dev
```

3. 安裝 mariadb C 語言 head
```bash
sudo apt install libmariadbclient-dev
```

4. 安裝 mysqlclient
```
pipenv install mysqlclient
```
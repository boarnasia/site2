# site2

このツールは指定したURLからファイルを取得し一枚の markdown (md) や PDF を作成します。

## behave の使い方

すべてのテストは `<project>/features` 以下にあります。

```shell
# すべてのテストを実行
$ rye run behave

# ファイルを指定して実行
$ rye run behave features/tutorial.feature

# タグを指定して実行
$ rye run behave -t @tutorial
$ rye run behave --tags @tutorial

# 対応ランゲージ一覧
$ rye run behave --lang-list
```

**デバッグの設定: VS Code**

デバッグをするときは steps/\*.py にBreak Pointを設定し、\*.featureファイルを開いた状態でデバッグを開始してください。

```json
{
    "version": "0.2.0",
    "configurations": [

        {
            "name": "Debug behave",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/.venv/bin/behave",
            "console": "integratedTerminal",
            "args": [
                "--no-capture",
                "--no-capture-stderr",  // 標準出力の表示
                "${file}"  // 現在開いている feature ファイル
            ]
        }
    ]
}
```

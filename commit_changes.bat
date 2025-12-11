@echo off
echo 正在添加所有更改的文件...
git add .

echo.
echo 正在提交更改...
git commit -m "更新README，强调跑团功能；删除多余文档；整合重要信息；添加背景介绍功能；优化CLI启动逻辑"

echo.
echo 提交完成！
echo.
echo 如果需要推送到远程仓库，请执行: git push
pause


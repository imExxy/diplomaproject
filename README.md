Приложение запускается с помощью Flask Run из среды Conda.
Состояние среды сохранено в YAML-файле condaenvexp2.yml, здесь показано, как из него создавать среду: https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file
При запуске также нужно запустить веб-сервер nginx (cd nginx-1.25.2 -> .\nginx.exe), и тогда приложение будет загружаться на localhost (по умолчанию, без указания портов).

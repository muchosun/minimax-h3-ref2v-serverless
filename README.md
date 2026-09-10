# MiniMax H3 REF2V — кандидат RunPod Serverless

Статус на 10 сентября: файлы сборки обновлены; образ ещё не собран.
Обычный A40 Pod прошёл два прогона, но это не тест Serverless-образа.
GitHub Integration RunPod не подключена (`githubAccountInfo: null`, проверено повторно).

Цель: около 300 секунд от отправки запроса до получения видео, включая холодный старт.
Начальный тест: 832×480, 124 кадра / 24 fps (~5.17 с), один фотореференс,
20 шагов. Это допущение для первого замера, не согласованный предел качества.
Прогон с фото и видео: 480×864, 141 кадр, 20 шагов — 604.690 секунды
в ComfyUI, 607.579 секунды до результата клиента. Модели уже были загружены.
Цель 300 секунд не достигнута; Turbo-профиль не проверен.

В образ включаются только REF2VA INT8, штатный 32B NVFP4 энкодер и два VAE:
42,470,585,471 байт (~39.56 GiB). FL2VA не скачивается. Скачивание и SHA256
проверка выполняются только при сборке; worker startup проверяет наличие и размер.
Обработчик API и возврат MP4/base64 предоставляет runpod/worker-comfyui 5.8.6.
ComfyUI v0.34.0 (commit `12d5279438bfefc058a269eae805ceab6047777f`),
CUDA 13 / PyTorch 2.11.0, torchvision 0.26.0, torchaudio 2.11.0.
Сборка выполняет pip check и CPU import smoke до скачивания моделей.
GPU-совместимость именно этого образа ещё не проверена.

## Основной маршрут — сборка и реестр RunPod

По предпочтению Александра используем GitHub Integration RunPod:
исходники и Dockerfile находятся в подключённом GitHub-репозитории,
сам образ собирает и хранит RunPod. Отдельный Docker Hub / GHCR не требуется.
Нужен репозиторий, к которому есть push-доступ и который доступен GitHub-интеграции
данного RunPod-аккаунта. Создан публичный репозиторий
https://github.com/muchosun/minimax-h3-ref2v-serverless (ветка main).
Push-доступ и наличие исходников подтверждены повторным чтением GitHub API.
RunPod → Settings → Connections → GitHub: подключить только этот репозиторий.
После подключения: New Endpoint → Import Git Repository → main → Dockerfile.
Сборка весов выполняется один раз до приёма пользовательских заданий.
Лимиты встроенной сборки: образ до 80 GB, docker build до 30 минут;
весь цикл до 160 минут. Фактический размер образа пока не измерен.
Источник: https://docs.runpod.io/serverless/workers/github-integration

Встроенный Cached Models — возможная альтернатива, но сейчас он скачивает все
варианты весов репозитория; на новом хосте ожидание скачивания увеличивает
клиентское время, хотя GPU за это ожидание не тарифицируется.
Источник: https://docs.runpod.io/serverless/endpoints/model-caching

## Резервный маршрут — собственный builder

Нужен Linux amd64 builder с Docker и минимум 160 GB свободного диска,
а также выбранный реестр с правом push. На этом Mac Docker не найден.
RunPod registry auth dockerhub-deityold подтверждает только настроенное скачивание
образов со стороны RunPod, не право локальной загрузки в этот реестр.

`docker build --platform linux/amd64 -t REGISTRY/PROJECT/minimax-h3-ref2v:20260910 .`

`docker push REGISTRY/PROJECT/minimax-h3-ref2v:20260910`

Перед деплоем зафиксировать digest собранного образа и установленный pip freeze.
Первое распространение большого образа на хосты также измеряется отдельно.

## Изолированный endpoint

Имя: alex-minimax-h3-ref2v-test-20260910. Workers min 0, max 1, FlashBoot on,
idle timeout 60s, execution timeout 1200s (диагностический предел, не целевой SLA),
container disk 100 GB, CUDA >=13.0. Первый кандидат GPU: RTX 5090;
если offload не укладывается в 300s, сравнить 48/80 GB с учётом цены за результат.
Не менять существующий production endpoint 9sdyt8e6xcxt0k.
RTX 5090 имеет 32 GB VRAM. Размер файлов весов не равен одновременно занятой
VRAM: компоненты могут загружаться последовательно и выгружаться в RAM.
Поэтому пригодность 5090 и выигрыш относительно A40 проверяются реальным заданием.

## Вход фото + видео

`python request.py reference.png --motion motion.mp4 --width 480 --height 864 --length 141 --prompt 'Appearance from <Picture 1>, movement from <Video 1>.' > request.json`

MP4 заранее привести к 24 fps. Входные файлы передаются в base64 через поле
`images` стандартного worker-comfyui; загрузка MP4 через этот Serverless handler
ещё требует проверки на собранном образе (обычный Pod загружал файл отдельно).
Личные фото/видео и request.json не публиковать в репозитории.
Локально проверены два unit-теста графа запроса, синтаксис shell и git diff --check.

## Проверка

1. Собрать и загрузить образ; подтвердить manifest digest в реестре.
2. На отдельном endpoint проверить модель и синтаксис Autogrow-входа через /object_info.
3. Сгенерировать запрос request.py, отправить /run, сохранить job id сразу.
4. Дождаться /status и MP4, проверить ffprobe, кадры, движение и соответствие референсу.
5. Отдельно измерить первый запрос после deployment, холодный запрос после scale-to-zero
   и повторный тёплый запрос: клиентское время, delayTime, executionTime, GPU и стоимость.
6. Бюджет 300s считать пройденным только по клиентскому времени с готовым скачанным MP4.
7. По окончании теста отключить тестовый endpoint и проверить отсутствие активных workers.

Источники:
- https://github.com/vincezh2000/minimax-h3-comfyui-serverless
- https://github.com/runpod-workers/worker-comfyui/tree/5.8.6
- https://github.com/Comfy-Org/ComfyUI/blob/v0.30.1/comfy_extras/nodes_minimax_h3.py
- https://huggingface.co/Comfy-Org/MiniMax-H3/tree/a98869194787969724c7425d95d0ed73ce9202af

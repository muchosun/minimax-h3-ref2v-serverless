# MiniMax H3 REF2V — кандидат RunPod Serverless

Статус: исходники подготовлены; образ ещё не собран и GPU-тест не выполнен.

Цель: около 300 секунд от отправки запроса до получения видео, включая холодный старт.
Начальный тест: 832×480, 124 кадра / 24 fps (~5.17 с), один фотореференс,
20 шагов. Это допущение для первого замера, не согласованный предел качества.
Видео-референс движения и ускоренный Turbo-профиль требуют следующего теста.

В образ включаются только REF2VA INT8, штатный 32B NVFP4 энкодер и два VAE:
42,470,585,471 байт (~39.56 GiB). FL2VA не скачивается. Скачивание и SHA256
проверка выполняются только при сборке; worker startup проверяет наличие и размер.
Обработчик API и возврат MP4/base64 предоставляет runpod/worker-comfyui 5.8.6.
ComfyUI v0.30.1, CUDA 13 / PyTorch 2.12.0. Сборка и совместимость ещё не проверены.

## Основной маршрут — сборка и реестр RunPod

По предпочтению Александра используем GitHub Integration RunPod:
исходники и Dockerfile находятся в подключённом GitHub-репозитории,
сам образ собирает и хранит RunPod. Отдельный Docker Hub / GHCR не требуется.
Нужен репозиторий, к которому есть push-доступ и который доступен GitHub-интеграции
данного RunPod-аккаунта. Такой репозиторий пока не подтверждён.
Сборка весов выполняется один раз до приёма пользовательских заданий.
Достаточность дискового лимита builder RunPod для этой сборки ещё не проверена.
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
idle timeout 60s, execution timeout 600s (диагностический предел, не целевой SLA),
container disk 100 GB, CUDA >=13.0. Первый кандидат GPU: RTX 5090;
если offload не укладывается в 300s, сравнить 48/80 GB с учётом цены за результат.
Не менять существующий production endpoint 9sdyt8e6xcxt0k.

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

# HTTP Transport Implementation Status

## Текущее состояние / Current Status

Этот документ описывает реализацию HTTP транспорта для YouTrack MCP сервера и текущие ограничения.

## Проблема / Issue

В текущей реализации есть проблема в коде `youtrack_mcp/server.py` - он пытается передать параметр `transport` в конструктор `FastMCP`, который не поддерживает этот параметр:

```python
# Строка 51-54 в youtrack_mcp/server.py
self.server = ToolServerBase(
    name=config.MCP_SERVER_NAME,
    instructions=config.MCP_SERVER_DESCRIPTION,
    transport=transport,  # ← Этот параметр не существует в FastMCP
)
```

### Ошибка / Error
```
TypeError: FastMCP.__init__() got an unexpected keyword argument 'transport'
```

## Решение / Solution

Созданы Docker конфигурации для HTTP транспорта, которые будут работать после исправления кода:

### 1. Dockerfile.http
Специализированный Dockerfile для HTTP режима:
- Экспортирует порт 8000
- Запускает сервер с `--transport http --host 0.0.0.0`
- Готов к использованию после исправления кода

### 2. Dockerfile.flexible  
Гибкий Dockerfile с поддержкой обоих режимов:
- Использует переменную окружения `MCP_TRANSPORT`
- Поддерживает stdio (по умолчанию) и http режимы
- Включает скрипт `docker-entrypoint.sh` для выбора режима

## Использование после исправления / Usage After Fix

### HTTP режим / HTTP Mode
```bash
# Сборка / Build
docker build -f Dockerfile.http -t youtrack-mcp-http .

# Запуск / Run
docker run --rm -p 8000:8000 \
  -e "YOUTRACK_API_TOKEN=your-token" \
  -e "YOUTRACK_URL=https://your.youtrack.cloud" \
  youtrack-mcp-http
```

### Гибкий режим / Flexible Mode
```bash
# Сборка / Build  
docker build -f Dockerfile.flexible -t youtrack-mcp-flexible .

# HTTP режим / HTTP mode
docker run --rm -p 8000:8000 \
  -e "MCP_TRANSPORT=http" \
  -e "YOUTRACK_API_TOKEN=your-token" \
  youtrack-mcp-flexible

# stdio режим / stdio mode
docker run --rm -i \
  -e "YOUTRACK_API_TOKEN=your-token" \
  youtrack-mcp-flexible
```

## Необходимые исправления кода / Required Code Fixes

Для работы HTTP транспорта нужно исправить `youtrack_mcp/server.py`:

1. Убрать параметр `transport` из конструктора FastMCP
2. Настроить FastMCP для HTTP режима через его поддерживаемые параметры

### Пример исправления / Fix Example
```python
# Вместо / Instead of:
self.server = ToolServerBase(
    name=config.MCP_SERVER_NAME,
    instructions=config.MCP_SERVER_DESCRIPTION,
    transport=transport,  # ← Убрать / Remove
)

# Использовать / Use:
if transport == "http":
    self.server = ToolServerBase(
        name=config.MCP_SERVER_NAME,
        instructions=config.MCP_SERVER_DESCRIPTION,
        host="0.0.0.0",
        port=8000,
    )
else:
    # stdio mode setup
    self.server = ToolServerBase(
        name=config.MCP_SERVER_NAME,
        instructions=config.MCP_SERVER_DESCRIPTION,
    )
```

## Тестирование / Testing

Скрипт `test-http-transport.sh` готов для тестирования после исправления кода:

```bash
# Установить переменную окружения / Set environment variable
export YOUTRACK_API_TOKEN=your-token

# Запустить тесты / Run tests
./test-http-transport.sh
```

## Документация / Documentation

Полная документация по HTTP транспорту доступна в `HTTP_TRANSPORT.md`.

## Заключение / Conclusion

Docker конфигурации для HTTP транспорта созданы и готовы к использованию. После исправления проблемы с параметром `transport` в `youtrack_mcp/server.py`, HTTP режим будет полностью функциональным.

The Docker configurations for HTTP transport have been created and are ready for use. After fixing the `transport` parameter issue in `youtrack_mcp/server.py`, HTTP mode will be fully functional.
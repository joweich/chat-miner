# Testing considerations

## How to run pytest
```
python3 -m pytest
```
## Test parsers
### Facebook Messenger

When adding a new test object in test/facebookMessenger/target.json, make sure that the ```hour``` attribute is in UTC-0. When running pytest, ```hour``` and ```timedate``` will be converted to the users timezone to avoid timezone errors.
# mymessage
Python Package for analyzing iMessage conversations stored on OSX

Using sqlite to query and organize chat transcripts stored in ~/Library/Messages/

## Installation

```
pip install git+git://github.com/noahshpak/mymessage 
```

### Usage
```python
from mymessage import messages
```
### Get Conversations
```python
convos = messages.get_convos()
```
### Looking at Vocabulary
```python
send_vocab = convos.sent_vocabulary()
```


Some code borrowed from https://github.com/mattrajca/pymessage-lite

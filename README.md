# CSSLoader-Mappings
Internal css mappings to translate css from older Steam clients to new ones


### Format:

```json
{
    "id": [
        "1",
        "2",
        "3"
    ]
}
```

- id: A randomly generated uuid. Currently serves no use.
- 1,2,3: The Steam classnames to map. All previous entries in the list will be mapped to the latest entry in the list.

### Updating translations (Webpack)

```js
const mappings = DFL.classMap.reduce((acc, cur) => {
    Object.entries(cur).forEach(([property, value]) => {
        if (acc[property]) {
            acc[property].push(value)
        } else {
            acc[property] = [value]   
        }
    })
    return acc
}, {})
```

+ webpack_mappings.py
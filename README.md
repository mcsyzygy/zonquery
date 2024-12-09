# zonquery
ZonQuery - A library for parsing selectors and building ASTs for JSON

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ZonQuery                                                                    ║
║  A library for parsing selectors and building ASTs for JSON data queries.    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
*** __WORK IN PROGRESS__ ***

This Python 3.12 library parses string selectors for extracting nodes from JSON
data and builds an Abstract Syntax Tree (AST) to be interpreted for node retrieval. 
The selector syntax is inspired by jQuery, CSS selectors, and AWK.

## Notable Features
- Supports function calls with or without arguments.
- Allows rich expressions with logical and relational operators, 
  adhering to operator precedence and associativity.
- Enables expression grouping using parentheses.
- Handles indexes and ranges for precise node targeting.
- Nested selectors are supported, including embedding within expressions.

## Current Status
- AST parser implementation is nearly complete.
- Interpreter implementation is pending and will be added soon.

## Dependencies
- Zero external dependencies.

## Sample Input and Output
- A couple of examples are listed below for reference.
- More examples are included in the unittest at the end of this file.

This library is designed to be lightweight (~600 lines), and self-contained.

### Example of a valid input selector
```
insurance {
    f:lookup(
        f:verify(
            this.plans.benefits.status {
                this.statusDetails = 'Vingt "Mille Lieues" sous les mers'
                } = 'Active Coverage',
            amount  <=  8_000
            type == MH
            ) 27 ! Visit NOT Percent )
    f:get_current_out_of_pocket("Year to Date", Remaining)
    f:validate_network(0, 3, 9, Rantanplan, 
            statusCode = 789, 
            foo = "Marsupilami & Fantasio",
            timePeriod <= 1234567)
    f:len  f:len2()  f:len3(   ) "f:len4"    (Athos Porthos Aramis)
}
.benefits [
     1
     2-9
     15-20
     33
  ]
.amounts {
  this.coInsurance{ insuranceType = "A" ~!!a && b} != this.plans{ 
    name = "Dental Care" }
}
.deductibles [0, -1]
```

### Another example selector and the resulting AST

#### INPUT
```
a {
    f:sin(
        f:max(
            this.kk1.jj2.ii3 {
                this.val1 = 'Vingt Mille Lieues sous les mers'
                } = 'jean valjean',
            z  <  3
            ) 3 π )
    f:min(11, 17)
}

.b [
     1
     2-9
     15-20
     33
  ]
```

#### OUTPUT
```
{
  "selector": [
    {
      "node": "a",
      "predicate": {
        "AND": [
          {
            "f:sin": [
              {
                "AND": [
                  {
                    "AND": [
                      {
                        "f:max": [
                          {
                            "=": [
                              {
                                "selector": [
                                  {"node": "this"},
                                  {"node": "kk1"},
                                  {"node": "jj2"},
                                  {
                                    "node": "ii3",
                                    "predicate": {
                                      "=": [
                                        {
                                          "selector": [
                                            {"node": "this"},
                                            {"node": "val1"} ] },
                                        "Vingt Mille Lieues sous les mers"
                                      ] } } ] },
                              "jean valjean"
                            ] },
                          {"<": ["z", "3"]}
                        ] },
                      "3"
                    ] },
                  "π"
                ] } ] },
          { "f:min": ["11", "17"] }
        ] } },
    {
      "node": "b",
      "ranges": [
        {"start": 1, "end": 1},
        {"start": 2, "end": 9},
        {"start": 15, "end": 20},
        {"start": 33, "end": 33} ] } ] }
```

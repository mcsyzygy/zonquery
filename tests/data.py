TEST_DATA: list[str] = [
    ### . ###
    r"""
# selector:
insurance {
    f:lookup(
        f:verify(
            this.plans.benefits.status {
                this.statusDetails = 'Vingt "Mille Lieues" sous les mers'
                } = 'Active Coverage',
            amount  <=  8_000
            type == MH
            ) 3 ! π NOT Percent  )
    f:get_current_out_of_pocket(11, 17)
    f:validate_network(0, 7, 9, Rantanplan,
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
  this.coInsurance{ insuranceType = "A" ~!!a && b} != this.plans{ name = "Dental Care" }
}
.deductibles [0, -1]

# ast:
{"selector": [
    {
      "node": "insurance",
      "predicate": {
        "AND": [
          {
            "AND": [
              {
                "AND": [
                  {
                    "AND": [
                      {
                        "AND": [
                          {
                            "AND": [
                              {
                                "AND": [
                                  {
                                    "f:lookup": [
                                      {
                                        "AND": [
                                          {
                                            "AND": [
                                              {
                                                "AND": [
                                                  {
                                                    "f:verify": [
                                                      {
                                                        "=": [
                                                          {
                                                            "selector": [
                                                              {"node": "this"},
                                                              {"node": "plans"},
                                                              {"node": "benefits"},
                                                              {
                                                                "node": "status",
                                                                "predicate": {
                                                                  "=": [
                                                                    {
                                                                      "selector": [
                                                                        {"node": "this"},
                                                                        {"node": "statusDetails"}
                                                                      ]},
                                                                    "Vingt \"Mille Lieues\" sous les mers"
                                                                  ]}}]},
                                                          "Active Coverage"
                                                        ]},
                                                      {
                                                        "AND": [
                                                          {"<=": ["amount", "8_000"]},
                                                          {"==": ["type", "MH"]}
                                                        ]}]},
                                                  "3"
                                                ]},
                                              {"!": ["π"]}
                                            ]},
                                          {"NOT": ["Percent"]}
                                        ]
                                      }
                                    ]
                                  },
                                  {"f:get_current_out_of_pocket": ["11", "17"]}
                                ]
                              },
                              {
                                "f:validate_network": [
                                  "0",
                                  "7",
                                  "9",
                                  "Rantanplan",
                                  {"=": ["statusCode", "789"]},
                                  {"=": ["foo", "Marsupilami & Fantasio"]},
                                  {"<=": ["timePeriod", "1234567"]}
                                ]}]},
                          {"f:len": []}
                        ]},
                      {"f:len2": []}
                    ]},
                  {"f:len3": []}
                ]},
              "f:len4"
            ]
          },
          {"AND": [{"AND": ["Athos", "Porthos"]}, "Aramis"]}
        ]}},
    {
      "node": "benefits",
      "ranges": [
        {"start": 1, "end": 1},
        {"start": 2, "end": 9},
        {"start": 15, "end": 20},
        {"start": 33, "end": 33}
      ]},
    {
      "node": "amounts",
      "predicate": {
        "!=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "coInsurance",
                "predicate": {
                  "&&": [
                    {
                      "AND": [
                        {"=": ["insuranceType", "A"]},
                        {"~": [{"!": [{"!": ["a"]}]}]}
                      ]},
                    "b"
                  ]}}]},
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"=": ["name", "Dental Care"]}}]}]}},
    {
      "node": "deductibles",
      "ranges": [
        {"start": 0, "end": 0},
        {"start": -1, "end": -1}]}]}
""",
    ### . ###
    """
# selector   :       a  .  b  .  c.   d      \t
# ast  :
{
  "selector": [
    { "node": "a" },
    { "node": "b" },
    { "node": "c" },
    { "node": "d" } ] }
""",
    ### . ###
    """
# selector:
a{3 OR 4    AND    2   777      AND ( 1 OR 5 )}

# ast:
{
  "selector": [
    {
      "node": "a",
      "predicate": {
        "OR": [
          "3",
          {
            "AND": [
              {"AND": [{"AND": ["4", "2"]}, "777"]},
              {"OR": ["1", "5"]} ] } ] } } ] }
    """,
    ### . ###
    """
# selector:  
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

# ast:
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
          { "f:min": ["11", "17"] } ] } },
    {
      "node": "b",
      "ranges": [
        {"start": 1, "end": 1},
        {"start": 2, "end": 9},
        {"start": 15, "end": 20},
        {"start": 33, "end": 33}
      ] } ] }        
""",
    ### . ###
    """
# selector:
a {
    f:sin(
        f:max(
            this.kk1.jj2.ii3 {
                this.val1 = 'Vingt Mille Lieues sous les mers'
                } = 'jean valjean',
            z  <  3
            ) 3 π )
    f:min(11, 17, 8, 9)
    f:len   (Athos Porthos Aramis)
}
.b [
     1
     2-9
     15-20
     33
  ]        

# ast:
{
  "selector": [
    {
      "node": "a",
      "predicate": {
        "AND": [
          {
            "AND": [
              {
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
                  {"f:min": ["11", "17", "8", "9"]}
                ] },
              {"f:len": []}
            ] },
          {"AND": [{"AND": ["Athos", "Porthos"]}, "Aramis"]}
        ] } },
    {
      "node": "b",
      "ranges": [
        {"start": 1, "end": 1},
        {"start": 2, "end": 9},
        {"start": 15, "end": 20},
        {"start": 33, "end": 33}
      ] } ] }
""",
    ### . ###
    """
# selector: n {3 AND NOT a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"NOT": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND NOT a NOT b}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          {"AND": ["3", {"NOT": ["a"]}]},
          {"NOT": ["b"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND ! a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"!": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND !a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"!": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 NOT a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"NOT": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 ! a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"!": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 !a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"!": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND NOT a NOT b}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          {"AND": ["3", {"NOT": ["a"]}]},
          {"NOT": ["b"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND !a !b}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          {"AND": ["3", {"!": ["a"]}]},
          {"!": ["b"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND NOT NOT a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          "3",
          {"NOT": [{"NOT": ["a"]}]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND !!a}
# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          "3",
          {
            "!": [
              {"!": ["a"]}
            ]}]}}]}
""",
    ### . ###
    """
# selector: n {3 !a !b}
# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          {"AND": ["3", {"!": ["a"]}]},
          {"!": ["b"]}]}}]}

""",
    ### . ###
    """
# selector: n {3 NOT NOT a}
# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          "3",
          {
            "NOT": [
              {"NOT": ["a"]}
            ]}]}}]}
""",
    ### . ###
    """
# selector: n {3 !!a}
# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          "3",
          {
            "!": [
              {"!": ["a"]}
            ]}]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{ name = "A" ~!!a && b} = this.plans{ name = "B" }  
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {
                  "&&": [
                    {
                      "AND": [
                        {"=": ["name", "A"]},
                        {"~": [{"!": [{"!": ["a"]}]}]}
                      ]},
                    "b"
                  ]}}]},
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"=": ["name", "B"]}}]}]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{ name = "A" ~!!a && b} != this.plans{ name = "B" }  
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "!=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {
                  "&&": [
                    {
                      "AND": [
                        {"=": ["name", "A"]},
                        {"~": [{"!": [{"!": ["a"]}]}]}
                      ]},
                    "b"
                  ]}}]},
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"=": ["name", "B"]}}]}]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{aaa} = bbb
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"aaa": []}
              }]},
          "bbb"]}}]}
""",
    ### . ###
    """
# selector: 
n {
  this.plans{a} = this.plans{b}
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {"node": "plans", "predicate": {"a": []}}
            ]},
          {
            "selector": [
              {"node": "this"},
              {"node": "plans", "predicate": {"b": []}}]}]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{ name = "A c d" } = B
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {"node": "plans", "predicate": {"=": ["name", "A c d"]}}
            ]},
          "B"]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{ name = "A c d" ~!!a && b} = this.plans{ name = B }
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {
                  "&&": [
                    {
                      "AND": [
                        {"=": ["name", "A c d"]},
                        {"~": [{"!": [{"!": ["a"]}]}]}
                      ]},
                    "b"
                  ]}}]},
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"=": ["name", "B"]}
              }]}]}}]}
""",
    ### . ###
    """
# selector: 
n {
  a != b
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {"!=": ["a", "b"]}
    }]}
""",
]

TEST_DATA_BUFFER: list[str] = [
    ### . ###
    """
    # selector:
    a { NOT b}
    # ast:
    {}
        """,
    ### . ###
    """
# selector: 
a { 
  a1{ b.c{ d.e = 3, z < 3 } = 4 } = v1 
}.a1.a2{}

# ast:
{}
""",
    ### . ###
    """
# selector: 
a { 
 f.max(
   this.b { bbb <= 1 } = "Vingt Mille Lieues sous les mers",
   z <= 3
 )

}.a1.a2{}

# ast:
{}
""",
    ### . ###
    """
# selector: 
n { 3 + 4 * 2 / ( 1 _ 5 ) ^ 2 ^ 3 }

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "+": [
          "3",
          {
            "/": [
              {"*": ["4", "2"]},
              {"^": [
                  {"_": ["1", "5"]},
                  {"^": ["2", "3"]}
                ]}
            ]
          }
        ]}}]}
    """,
    ### . ###
    ### . ###
    ### . ###
    ### . ###
    ### . ###
]

SELECTOR_SAMPLE: str = """
        a.b{f:f1 f:f2 (f:f3 OR f:f4) f:f5}.c[1-3, 7, f:f5]

        # Is that really needed? Doesn't seem so
        a.b{f:f1 f:f2 (f:f3 OR f:f4) f:f5}.c[1-3, 7, f:f5]:node

        a.b{f:f1 f:f2 (f:f3 OR v=w1 w2 w3) f:f5}.c[1-3, 7, f:f5]

        a.b{f:f1 f:f2 (f:f3 OR v="w1 w2 w3 'w4' \"w5\" w6") f:f5}.c[1-3, 7, f:f5]

        a.b.c{d.e.k = 3 AND x.y > 5}

        a.b.c{f:f1 = 137 AND f:f2(p1, p2) = "  abc... z  "}

        DEFINITION: def f:f1(node, context, a, b, c,  …)

raw.1659.plans[0].benefits[8].status
raw.[1659].plans[0].benefits[8].status
raw.[1659].plans[0].benefits[8].status
raw.1659.plans{name = ABC}.benefits[8].status
raw.1659.plans{f:has_name}.benefits[8].status
raw.1659.plans{f:has_name(plan = ABC)}.benefits[8].status
raw.1659.plans{ name = ABC }.benefits[8].status
raw.1659.plans{ name == ABC }.benefits[8].status
raw.1659.plans{ name > 1 }.benefits[8].status
raw.1659.plans{ name != 1 }.benefits[8].status
raw.1659.plans{ name < 1 }.benefits[8].status
raw.1659.plans{ name = ABC }.benefits[0, 1-5, 8].status
raw.1659.plans{ name = ABC }.benefits[*].status
raw.1659.plans{ name = ABC }.benefits[a.b.c = 123].status
raw.1659.plans{ name = ABC, type = 123 }.benefits[8].status
raw.1659.plans{ name = ABC AND type = 123 }.benefits[8].status
raw.1659.plans{ name = ABC OR type = 123 }.benefits[8].status
raw.1659.plans{ name = ABC -type = 123 }.benefits[8].status
raw.1659.plans{ name = ABC NOT type = 123 }.benefits[8].status
raw.1659.plans[0].benefits[8].status
"""

MORE_SELECTOR_SAMPLE: tuple[tuple[str, list[str]] | tuple[int, int], ...] = (
    ("  a  .  b  .  c.   d   ", ["a", "b", "c", "d"]),
    ("a{(3 OR 4) AND (2 OR 1)}", []),
    ("a{3 OR 4 AND 2 AND ( 1 OR 5 )}", []),
    ("a{3 OR 4    AND    2   777      AND ( 1 OR 5 )}", []),
    ("a{f:sin( f:max( 2, 3 ) AND 3 AND π )}", []),
    ("a{f:sin( f:max( 2, 3 ) 3 π ) f:min(11, 17)}", []),
    ("a{f:sin( f:max( x =  2, z  <  3  ) 3 π ) f:min(11, 17)}", []),
    ("a{f:sin( f:max( k.j.i =  2, z  <  3  ) 3 π ) f:min(11, 17)}", []),
    (
        "a{f:sin( f:max( kk1.jj2.ii3 = 'jean valjean', z  <  3  ) 3 π ) f:min(11, 17)}.b[1, 2-9 15-20   ,   33]",
        [],
    ),
    (
        "a{f:sin( f:max( this.kk1.jj2.ii3{this.val1 = 'Vingt Mille Lieues sous les mers'} = 'jean valjean', z  <  3  ) 3 π ) f:min(11, 17)}.b[1, 2-9 15-20   ,   33]",
        [],
    ),
    (0, 0),
    (
        """
        a {
            f:sin(
                f:max(
                    this.kk1.jj2.ii3 {
                        this.val1 = 'Vingt Mille Lieues sous les mers'
                        } = 'jean valjean',
                    z  <  3
                    ) 3 π )
            f:min(11, 17)
            f:len (Athos Porthos Aramis)
        }

        .b [
             1
             2-9
             15-20
             33
          ]            
        """,
        [],
    ),
    (
        "a{f:sin( f:max( kk1.jj2.ii3 =  2, z  <  3  ) 3 π ) f:min(11, 17)}.b[1, 2-9 15-20, 33]",
        [],
    ),
    ("a{f:sin( f:max( 2, 3 ) AND 3 AND π ) f:min(11, 17)}", []),
    (0, 0),
    ("  a{f:f1(x, y) f:f2(k1, k2) (A OR B) k = ABC}", []),
    (1, 1),
    ("  a.b.c.d   ", ["a", "b", "c", "d"]),
    ("  a.b[1, 2-9 15-20, 33].c.d[2, 3-9]   ", []),
    (0, 0),
    (
        "  a.b{f:f1(x, y) f:f2(k1, k2) (A OR B) k = ABC}.c.d[1, 2-9 15-20, 33]   ",
        [],
    ),
    (
        "  a.b{f:f1(x = 1, y) f:f2(k1, k2) (A OR B) k = ABC}.c.d[1, 2-9 15-20, 33]   ",
        [],
    ),
    ("  a.b{f:f1 f:f2 (A OR B) k = ABC}.c.d[1, 2-9 15-20, 33]   ", []),
    (1, 1),
    (
        "  a.b  {  f:f1 f:f2 (A OR B) f:f3(a = 1, b=2)} .c.d   ",
        ["a", "b", "c", "d"],
    ),
    (
        'a.b{f:f1 f:f2 (f:f3 OR v="w1 w2 w3 \'w4\' " w5 " w6") f:f5}.c[1-3, 7, f:f5]',
        [],
    ),
    (
        'a.b  {   f:f1 f:f2 (   f:f3 OR v="w1 w2 w3 \'w4\' " w5 " w6") f:f5  } .c   [   1-3, 7, f:f5]',
        [],
    ),
    ("a.b{f:f1  f:f2 (f:f3 OR f:f4) f5}.c[1-3,  7 , f5]", []),
    ("  a.b {f:f1  f:f2 (f:f3 OR f:f4) f5}.c [1-3,  7 , f5]  ", []),
    ("a.b{f:f1  f:f2 (f:f3 AND (f:f4 OR w0)) f5}.c[1-3,  7 , f5]", []),
    ("a.b{f:f1  f:f2 (f:f3 AND(f:f4 OR w0)) f5}.c[1-3,  7 , f5]", []),
    ("a.b{f:f1 f:f2 (f:f3 OR v=w1 w2 w3) f:f5}.c[1-3, 7, f:f5]", []),
    (
        'a.b{f:f1 f:f2 (f:f3 OR v="w1 w2 w3 \'w4\' "w5" w6") f:f5}.c[1-3, 7, f:f5]',
        [],
    ),
    ("a.b.c{d.e.k = 3 AND x.y > 5}", []),
    ('a.b.c{f:f1 = 137 AND f:f2(p1, p2) = "  abc... z  "}', []),
)

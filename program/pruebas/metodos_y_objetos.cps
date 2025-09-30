function toString(x: integer): string { return ""; }

class Counter {
  let value: integer;

  function constructor(init: integer) { this.value = init; }

  function inc(): integer {
    this.value = this.value + 1;
    return this.value;
  }

  function add(delta: integer): integer {
    this.value = this.value + delta;
    return this.value;
  }
}

let log: string = "";

let c: Counter = new Counter(0);
let r: integer = c.inc();       
r = r + c.add(3);               
r = r + c.inc();               
log = log + "r=" + toString(r) + ", value=" + toString(c.value) + "\n";

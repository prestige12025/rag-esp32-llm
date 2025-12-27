import sys
import json
from pathlib import Path

from rag.validate import VALIDATE_MAP, validate_common
from rag.core import ValidationResult


def detect_rule_key(text: str) -> str:
    t = text.lower()

    has_i2c = any(k in t for k in ("i2c", "wire", "sda", "scl"))
    has_spi = any(k in t for k in ("spi", "miso", "mosi", "sck"))

    if has_i2c and has_spi:
        return "i2c_spi"
    if has_i2c:
        return "i2c"
    if has_spi:
        return "spi"
    return "default"


def resolve_validators(rule_key: str):
    validators = [validate_common]

    v = VALIDATE_MAP.get(rule_key)
    if callable(v):
        validators.append(v)

    return validators


def main(argv=None):
    argv = argv or sys.argv[1:]

    use_json = "--json" in argv
    verbose = "--verbose" in argv
    quiet = "--quiet" in argv

    # --rule handling
    if "--rule" in argv:
        i = argv.index("--rule")
        try:
            rule_key = argv[i + 1]
        except IndexError:
            sys.stderr.write("unknown rule\n")
            sys.exit(2)

        if rule_key not in VALIDATE_MAP and rule_key != "default":
            sys.stderr.write("unknown rule\n")
            sys.exit(2)

        argv = argv[:i] + argv[i + 2:]
    else:
        rule_key = None

    try:
        path = Path(argv[0])
        text = path.read_text(encoding="utf-8")

        if rule_key is None:
            rule_key = detect_rule_key(text)

        validators = resolve_validators(rule_key)

        results: list[ValidationResult] = []
        for v in validators:
            results.extend(v(text))

        errors = [r for r in results if r.severity == "error"]

        if use_json:
            payload = {
                "status": "ng" if errors else "ok",
                "rule": rule_key,
                "errors": [r.message for r in errors],
            }
            sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        else:
            if verbose:
                sys.stdout.write(f"[INFO] detected rule: {rule_key}\n")

            if errors:
                for e in errors:
                    sys.stdout.write(f"[NG] {e.message}\n")
            else:
                if not quiet:
                    sys.stdout.write("[OK] validation passed\n")

        sys.stdout.flush()
        sys.exit(1 if errors else 0)

    except Exception as e:
        if use_json:
            payload = {
                "status": "ng",
                "rule": "unknown",
                "errors": [str(e)],
            }
            sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        else:
            sys.stderr.write(str(e) + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

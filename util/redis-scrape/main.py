import json
from redis import StrictRedis


def main():
    print("ensure you port forwarded redis, if this fails, thats probably why :)")

    client = StrictRedis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
    )

    out = {}

    # dont do this. seriously. but... like... its not a big deal ok?
    for key in client.scan_iter("*"):
        try:
            key_type = client.type(key)
            if key_type == "string":
                out[key] = client.get(key)
            elif key_type == "list":
                out[key] = client.lrange(key, 0, -1)
            elif key_type == "set":
                out[key] = list(client.smembers(key))
            elif key_type == "hash":
                out[key] = client.hgetall(key)
            elif key_type == "zset":
                out[key] = client.zrange(key, 0, -1, withscores=True)
            else:
                out[key] = f"<{key_type} not handled>"
        except Exception as e:
            out[key] = f"Error: {e}"

    print(json.dumps(out, indent=4))


if __name__ == "__main__":
    main()

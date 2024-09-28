import functools
import traceback

from fastapi import HTTPException, status


def logging_decorator(func):
    @functools.wraps(func)
    def _wrapper(*args, log_list: list = None, **kwargs):
        func_name = func.__name__
        if log_list is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"type": "implement error", func_name: "log_list is not exists"},
            )

        log_list.append(f"> exec_function: {func_name}...")

        try:
            result = func(*args, **kwargs)
            log_list[-1] += f"OK. result: {result}"
            return result
        except Exception as e:
            log_list[-1] += "Exception."
            log_list.append(f"> reason: {e}")
            tb_list = traceback.format_exception(type(e), e, e.__traceback__)
            for tb in tb_list:
                tb = tb.strip("\n")
                if "fastapi.exceptions.HTTPException" in tb:
                    # 前回起きたエラーレスポンスを含むので読み飛ばす
                    log_list.append(">> " + "    ...)")

                elif "\n" in tb:
                    log_list.extend([">> " + line for line in tb.split("\n")])
                else:
                    log_list.append(">> " + tb)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=log_list
            ) from None

    return _wrapper


@logging_decorator
def func_a(x, y, log_list=None):
    return x + y


@logging_decorator
def func_b(x, y, log_list=None):
    return x * y


@logging_decorator
def func_c(x, y, log_list=None):
    return x / y  # y:0 -> exception


if __name__ == "__main__":
    stack = []

    func_a(1, 2, log_list=stack)
    func_b(3, 4, log_list=stack)
    func_c(5, 0, log_list=stack)  # exception
    func_c(10, 2, log_list=stack)

    for log in stack:
        print(log)

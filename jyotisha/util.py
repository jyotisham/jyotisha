def zero_if_none(x):
  return default_if_none(x=x, default=0)

def default_if_none(x, default):
  return default if x is None else x

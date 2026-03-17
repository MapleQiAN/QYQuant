SUPPORTED_PACKAGES = [
    {
        "name": "pandas",
        "version": "2.x",
        "description": "数据处理与时间序列分析",
    },
    {
        "name": "numpy",
        "version": "1.26.x",
        "description": "数值计算与数组运算",
    },
    {
        "name": "ta-lib",
        "version": "0.4.x",
        "description": "常用技术指标计算",
    },
    {
        "name": "scipy",
        "version": "1.x",
        "description": "科学计算与优化工具",
    },
    {
        "name": "sklearn",
        "version": "1.x",
        "description": "机器学习算法与预处理",
    },
]


def get_supported_packages() -> list[dict[str, str]]:
    return [dict(item) for item in SUPPORTED_PACKAGES]

PULSE_NAME = [
    '呼吸',
    '潮汐',
    '连击',
    '快速按捏',
    '按捏渐强',
    '心跳节奏',
    '压缩',
    '节奏步伐',
    '颗粒摩擦',
    '渐变弹跳',
    '波浪涟漪',
    '雨水冲刷',
    '变速敲击',
    '信号灯',
    '挑逗1',
    '挑逗2'
]

PULSE_DATA = {
    '呼吸': [
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 5, 10, 20)),
        ((10, 10, 10, 10), (20, 25, 30, 40)), ((10, 10, 10, 10), (40, 45, 50, 60)),
        ((10, 10, 10, 10), (60, 65, 70, 80)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((0, 0, 0, 0), (0, 0, 0, 0)), ((0, 0, 0, 0), (0, 0, 0, 0)), ((0, 0, 0, 0), (0, 0, 0, 0))
    ],
    '潮汐': [
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 4, 8, 17)),
        ((10, 10, 10, 10), (17, 21, 25, 33)), ((10, 10, 10, 10), (50, 50, 50, 50)),
        ((10, 10, 10, 10), (50, 54, 58, 67)), ((10, 10, 10, 10), (67, 71, 75, 83)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 98, 96, 92)),
        ((10, 10, 10, 10), (92, 90, 88, 84)), ((10, 10, 10, 10), (84, 82, 80, 76)),
        ((10, 10, 10, 10), (68, 68, 68, 68))
    ],
    '连击': [
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 92, 84, 67)),
        ((10, 10, 10, 10), (67, 58, 50, 33)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 0, 0, 1)), ((10, 10, 10, 10), (2, 2, 2, 2))
    ],
    '快速按捏': [
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((0, 0, 0, 0), (0, 0, 0, 0))
    ],
    '按捏渐强': [
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (29, 29, 29, 29)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (52, 52, 52, 52)),
        ((10, 10, 10, 10), (2, 2, 2, 2)), ((10, 10, 10, 10), (73, 73, 73, 73)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (87, 87, 87, 87)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (0, 0, 0, 0))
    ],
    '心跳节奏': [
        ((110, 110, 110, 110), (100, 100, 100, 100)), ((110, 110, 110, 110), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (75, 75, 75, 75)),
        ((10, 10, 10, 10), (75, 77, 79, 83)), ((10, 10, 10, 10), (83, 85, 88, 92)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 0, 0, 0))
    ],
    '压缩': [
        ((25, 25, 24, 24), (100, 100, 100, 100)), ((24, 23, 23, 23), (100, 100, 100, 100)),
        ((22, 22, 22, 21), (100, 100, 100, 100)), ((21, 21, 20, 20), (100, 100, 100, 100)),
        ((20, 19, 19, 19), (100, 100, 100, 100)), ((18, 18, 18, 17), (100, 100, 100, 100)),
        ((17, 16, 16, 16), (100, 100, 100, 100)), ((15, 15, 15, 14), (100, 100, 100, 100)),
        ((14, 14, 13, 13), (100, 100, 100, 100)), ((13, 12, 12, 12), (100, 100, 100, 100)),
        ((11, 11, 11, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100))
    ],
    '节奏步伐': [
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 5, 10, 20)),
        ((10, 10, 10, 10), (20, 25, 30, 40)), ((10, 10, 10, 10), (40, 45, 50, 60)),
        ((10, 10, 10, 10), (60, 65, 70, 80)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 6, 12, 25)),
        ((10, 10, 10, 10), (25, 31, 38, 50)), ((10, 10, 10, 10), (50, 56, 62, 75)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 8, 16, 33)), ((10, 10, 10, 10), (33, 42, 50, 67)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 12, 25, 50)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (100, 100, 100, 100))
    ],
    '颗粒摩擦': [
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (0, 0, 0, 0))
    ],
    '渐变弹跳': [
        ((10, 10, 10, 10), (1, 1, 1, 1)), ((10, 10, 10, 10), (1, 9, 18, 34)),
        ((10, 10, 10, 10), (34, 42, 50, 67)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((0, 0, 0, 0), (0, 0, 0, 0)), ((0, 0, 0, 0), (0, 0, 0, 0))
    ],
    '波浪涟漪': [
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 12, 25, 50)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (73, 73, 73, 73))
    ],
    '雨水冲刷': [
        ((10, 10, 10, 10), (34, 34, 34, 34)), ((10, 10, 10, 10), (34, 42, 50, 67)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((0, 0, 0, 0), (0, 0, 0, 0)),
        ((0, 0, 0, 0), (0, 0, 0, 0))
    ],
    '变速敲击': [
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((110, 110, 110, 110), (100, 100, 100, 100)),
        ((110, 110, 110, 110), (100, 100, 100, 100)), ((110, 110, 110, 110), (100, 100, 100, 100)),
        ((110, 110, 110, 110), (100, 100, 100, 100)), ((0, 0, 0, 0), (0, 0, 0, 0))
    ],
    '信号灯': [
        ((197, 197, 197, 197), (100, 100, 100, 100)), ((197, 197, 197, 197), (100, 100, 100, 100)),
        ((197, 197, 197, 197), (100, 100, 100, 100)), ((197, 197, 197, 197), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 8, 16, 33)),
        ((10, 10, 10, 10), (33, 42, 50, 67)), ((10, 10, 10, 10), (100, 100, 100, 100))
    ],
    '挑逗1': [
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 6, 12, 25)),
        ((10, 10, 10, 10), (25, 31, 38, 50)), ((10, 10, 10, 10), (50, 56, 62, 75)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 0, 0, 0)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((10, 10, 10, 10), (100, 100, 100, 100))
    ],
    '挑逗2': [
        ((10, 10, 10, 10), (1, 1, 1, 1)), ((10, 10, 10, 10), (1, 4, 6, 12)),
        ((10, 10, 10, 10), (12, 15, 18, 23)), ((10, 10, 10, 10), (23, 26, 28, 34)),
        ((10, 10, 10, 10), (34, 37, 40, 45)), ((10, 10, 10, 10), (45, 48, 50, 56)),
        ((10, 10, 10, 10), (56, 59, 62, 67)), ((10, 10, 10, 10), (67, 70, 72, 78)),
        ((10, 10, 10, 10), (78, 81, 84, 89)), ((10, 10, 10, 10), (100, 100, 100, 100)),
        ((10, 10, 10, 10), (100, 100, 100, 100)), ((10, 10, 10, 10), (0, 0, 0, 0)),
        ((0, 0, 0, 0), (0, 0, 0, 0))
    ]
}
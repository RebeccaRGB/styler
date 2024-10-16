# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test project behavior")

    LINE = 0
    CTRL = 1
    BMAP = 2
    ATTR = 4

    async def sty_write(a, d):
        # Set address and data
        dut.ui_in.value = 0xC0 | a
        dut.uio_in.value = d & 0xFF
        await ClockCycles(dut.clk, 1)
        # Enable write
        dut.ui_in.value = 0x40 | a
        await ClockCycles(dut.clk, 1)
        # Disable write
        dut.ui_in.value = 0xC0 | a
        await ClockCycles(dut.clk, 1)

    async def sty_read(a):
        # Enable output
        dut.ui_in.value = 0x80 | a
        await ClockCycles(dut.clk, 1)
        r1 = dut.uo_out.value & 0xFF
        r2 = dut.uio_out.value & 0xFF
        # Disable output
        dut.ui_in.value = 0xC0 | a
        await ClockCycles(dut.clk, 1)
        assert r1 == r2
        return r1

    async def bmp_write(a, d):
        await sty_write(a | BMAP | 0, d >> 0)
        await sty_write(a | BMAP | 1, d >> 8)

    async def bmp_read(a):
        b1 = await sty_read(a | BMAP | 0)
        b2 = await sty_read(a | BMAP | 1)
        return (b1 << 0) | (b2 << 8)

    assert await sty_read(LINE) == 0
    assert await sty_read(CTRL) == 0x3C
    assert await bmp_read(0) == 0

    await sty_write(LINE, 15)
    await sty_write(CTRL, 0x3F)
    await bmp_write(0, 0xFFFF)

    assert await sty_read(LINE) == 15
    assert await sty_read(CTRL) == 0x3F
    assert await bmp_read(0) == 0xFFFF

    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.

    FAINT_PHASE      = 0x08
    BLINK_PHASE      = 0x10
    CURSOR           = 0x20

    CURSOR_BOTTOM    = 0x01
    CURSOR_TOP       = 0x02
    CURSOR_EDGES     = 0x03
    CURSOR_BLINK     = 0x04
    CURSOR_ENABLE    = 0x08
    LINE_ENABLE      = 0x10
    BLINK_ENABLE     = 0x20
    CTRL_DEFAULT     = 0x3C

    X_OFFSET         = 0x00000001
    X_WIDTH          = 0x00000002
    Y_OFFSET         = 0x00000004
    Y_WIDTH          = 0x00000008
    X_PREMIRROR      = 0x00000010
    X_POSTMIRROR     = 0x00000020
    Y_PREMIRROR      = 0x00000040
    Y_POSTMIRROR     = 0x00000080
    BOLD             = 0x00000100
    FAINT            = 0x00000200
    ITALIC           = 0x00000400
    REVERSE_ITALIC   = 0x00000800
    BLINK            = 0x00001000
    ALTERNATE        = 0x00002000
    INVERSE          = 0x00004000
    HIDDEN           = 0x00008000
    UNDERLINE        = 0x00010000
    DOUBLE_UNDERLINE = 0x00020000
    DOTTED_UNDERLINE = 0x00040000
    STRIKE           = 0x00080000
    DOUBLE_STRIKE    = 0x00100000
    DOTTED_STRIKE    = 0x00200000
    OVERLINE         = 0x00400000
    DOUBLE_OVERLINE  = 0x00800000
    DOTTED_OVERLINE  = 0x01000000

    async def sty_test(phase, ctrl, attr, bmp):
        await sty_write(phase | CTRL, ctrl)
        await sty_write(phase | ATTR | 0, attr >> 0)
        await sty_write(phase | ATTR | 1, attr >> 8)
        await sty_write(phase | ATTR | 2, attr >> 16)
        await sty_write(phase | ATTR | 3, attr >> 24)
        for phy_line in range(0, 16):
            await sty_write(phase | LINE, phy_line)
            log_line = await sty_read(phase | LINE)
            await bmp_write(phase, bmp[log_line * 2])
            res_bmp = await bmp_read(phase)
            assert res_bmp == bmp[phy_line * 2 + 1]

    NO_CHANGE = [
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
        0b0011111111110000, 0b0011111111110000,
        0b0011000000011000, 0b0011000000011000,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000011000, 0b0011000000011000,
        0b0011111111110000, 0b0011111111110000,
        0b0011000011000000, 0b0011000011000000,
        0b0011000001100000, 0b0011000001100000,
        0b0011000000110000, 0b0011000000110000,
        0b0011000000011000, 0b0011000000011000,
        0b0011000000001100, 0b0011000000001100,
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
    ]

    INVERTED = [
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
        0b0011111111110000, 0b1100000000001111,
        0b0011000000011000, 0b1100111111100111,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000011000, 0b1100111111100111,
        0b0011111111110000, 0b1100000000001111,
        0b0011000011000000, 0b1100111100111111,
        0b0011000001100000, 0b1100111110011111,
        0b0011000000110000, 0b1100111111001111,
        0b0011000000011000, 0b1100111111100111,
        0b0011000000001100, 0b1100111111110011,
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
    ]

    INVERTED_TOP = [
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
        0b0011111111110000, 0b1100000000001111,
        0b0011000000011000, 0b0011000000011000,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000011000, 0b0011000000011000,
        0b0011111111110000, 0b0011111111110000,
        0b0011000011000000, 0b0011000011000000,
        0b0011000001100000, 0b0011000001100000,
        0b0011000000110000, 0b0011000000110000,
        0b0011000000011000, 0b0011000000011000,
        0b0011000000001100, 0b0011000000001100,
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
    ]

    INVERTED_BOTTOM = [
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
        0b0011111111110000, 0b0011111111110000,
        0b0011000000011000, 0b0011000000011000,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000011000, 0b0011000000011000,
        0b0011111111110000, 0b0011111111110000,
        0b0011000011000000, 0b0011000011000000,
        0b0011000001100000, 0b0011000001100000,
        0b0011000000110000, 0b0011000000110000,
        0b0011000000011000, 0b0011000000011000,
        0b0011000000001100, 0b1100111111110011,
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
    ]

    INVERTED_EDGES = [
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
        0b0011111111110000, 0b1100000000001111,
        0b0011000000011000, 0b0011000000011000,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000001100, 0b0011000000001100,
        0b0011000000011000, 0b0011000000011000,
        0b0011111111110000, 0b0011111111110000,
        0b0011000011000000, 0b0011000011000000,
        0b0011000001100000, 0b0011000001100000,
        0b0011000000110000, 0b0011000000110000,
        0b0011000000011000, 0b0011000000011000,
        0b0011000000001100, 0b1100111111110011,
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
    ]

    INVERTED_NORMAL_TOP = [
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
        0b0011111111110000, 0b0011111111110000,
        0b0011000000011000, 0b1100111111100111,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000011000, 0b1100111111100111,
        0b0011111111110000, 0b1100000000001111,
        0b0011000011000000, 0b1100111100111111,
        0b0011000001100000, 0b1100111110011111,
        0b0011000000110000, 0b1100111111001111,
        0b0011000000011000, 0b1100111111100111,
        0b0011000000001100, 0b1100111111110011,
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
    ]

    INVERTED_NORMAL_BOTTOM = [
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
        0b0011111111110000, 0b1100000000001111,
        0b0011000000011000, 0b1100111111100111,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000011000, 0b1100111111100111,
        0b0011111111110000, 0b1100000000001111,
        0b0011000011000000, 0b1100111100111111,
        0b0011000001100000, 0b1100111110011111,
        0b0011000000110000, 0b1100111111001111,
        0b0011000000011000, 0b1100111111100111,
        0b0011000000001100, 0b0011000000001100,
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
    ]

    INVERTED_NORMAL_EDGES = [
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
        0b0011111111110000, 0b0011111111110000,
        0b0011000000011000, 0b1100111111100111,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000001100, 0b1100111111110011,
        0b0011000000011000, 0b1100111111100111,
        0b0011111111110000, 0b1100000000001111,
        0b0011000011000000, 0b1100111100111111,
        0b0011000001100000, 0b1100111110011111,
        0b0011000000110000, 0b1100111111001111,
        0b0011000000011000, 0b1100111111100111,
        0b0011000000001100, 0b0011000000001100,
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
    ]

    #              cursor/phase        control register                                       attributes         result
    await sty_test(0,                  0,                                                     0,                 NO_CHANGE)
    await sty_test(0,                  CURSOR_BLINK,                                          0,                 NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE,                                         0,                 NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_TOP,                              0,                 NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BOTTOM,                           0,                 NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_EDGES,                            0,                 NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK,                            0,                 NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 0,                 NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              0,                 NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        0,                                                     0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_BLINK,                                          0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE,                                         0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_TOP,                              0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BOTTOM,                           0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_EDGES,                            0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK,                            0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              0,                 NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               0,                 NO_CHANGE)
    await sty_test(CURSOR,             0,                                                     0,                 NO_CHANGE)
    await sty_test(CURSOR,             CURSOR_BLINK,                                          0,                 NO_CHANGE)
    await sty_test(CURSOR,             CURSOR_ENABLE,                                         0,                 INVERTED)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_TOP,                              0,                 INVERTED_TOP)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BOTTOM,                           0,                 INVERTED_BOTTOM)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_EDGES,                            0,                 INVERTED_EDGES)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK,                            0,                 INVERTED)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 0,                 INVERTED_TOP)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              0,                 INVERTED_BOTTOM)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               0,                 INVERTED_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, 0,                                                     0,                 NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_BLINK,                                          0,                 NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE,                                         0,                 INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_TOP,                              0,                 INVERTED_TOP)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BOTTOM,                           0,                 INVERTED_BOTTOM)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_EDGES,                            0,                 INVERTED_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK,                            0,                 NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 0,                 NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              0,                 NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               0,                 NO_CHANGE)

    #              cursor/phase        control register                                       attributes         result
    await sty_test(0,                  0,                                                     INVERSE,           INVERTED)
    await sty_test(0,                  CURSOR_BLINK,                                          INVERSE,           INVERTED)
    await sty_test(0,                  CURSOR_ENABLE,                                         INVERSE,           INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_TOP,                              INVERSE,           INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BOTTOM,                           INVERSE,           INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_EDGES,                            INVERSE,           INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK,                            INVERSE,           INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 INVERSE,           INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              INVERSE,           INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        0,                                                     INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_BLINK,                                          INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE,                                         INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_TOP,                              INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BOTTOM,                           INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_EDGES,                            INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK,                            INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              INVERSE,           INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               INVERSE,           INVERTED)
    await sty_test(CURSOR,             0,                                                     INVERSE,           INVERTED)
    await sty_test(CURSOR,             CURSOR_BLINK,                                          INVERSE,           INVERTED)
    await sty_test(CURSOR,             CURSOR_ENABLE,                                         INVERSE,           NO_CHANGE)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_TOP,                              INVERSE,           INVERTED_NORMAL_TOP)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BOTTOM,                           INVERSE,           INVERTED_NORMAL_BOTTOM)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_EDGES,                            INVERSE,           INVERTED_NORMAL_EDGES)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK,                            INVERSE,           NO_CHANGE)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 INVERSE,           INVERTED_NORMAL_TOP)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              INVERSE,           INVERTED_NORMAL_BOTTOM)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               INVERSE,           INVERTED_NORMAL_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, 0,                                                     INVERSE,           INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_BLINK,                                          INVERSE,           INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE,                                         INVERSE,           NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_TOP,                              INVERSE,           INVERTED_NORMAL_TOP)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BOTTOM,                           INVERSE,           INVERTED_NORMAL_BOTTOM)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_EDGES,                            INVERSE,           INVERTED_NORMAL_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK,                            INVERSE,           INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 INVERSE,           INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              INVERSE,           INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               INVERSE,           INVERTED)

    #              cursor/phase        control register                                       attributes         result
    await sty_test(0,                  0,                                                     ALTERNATE,         INVERTED)
    await sty_test(0,                  CURSOR_BLINK,                                          ALTERNATE,         INVERTED)
    await sty_test(0,                  CURSOR_ENABLE,                                         ALTERNATE,         INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_TOP,                              ALTERNATE,         INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BOTTOM,                           ALTERNATE,         INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_EDGES,                            ALTERNATE,         INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK,                            ALTERNATE,         INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 ALTERNATE,         INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              ALTERNATE,         INVERTED)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        0,                                                     ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_BLINK,                                          ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE,                                         ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_TOP,                              ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BOTTOM,                           ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_EDGES,                            ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK,                            ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               ALTERNATE,         INVERTED)
    await sty_test(CURSOR,             0,                                                     ALTERNATE,         INVERTED)
    await sty_test(CURSOR,             CURSOR_BLINK,                                          ALTERNATE,         INVERTED)
    await sty_test(CURSOR,             CURSOR_ENABLE,                                         ALTERNATE,         NO_CHANGE)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_TOP,                              ALTERNATE,         INVERTED_NORMAL_TOP)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BOTTOM,                           ALTERNATE,         INVERTED_NORMAL_BOTTOM)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_EDGES,                            ALTERNATE,         INVERTED_NORMAL_EDGES)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK,                            ALTERNATE,         NO_CHANGE)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 ALTERNATE,         INVERTED_NORMAL_TOP)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              ALTERNATE,         INVERTED_NORMAL_BOTTOM)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               ALTERNATE,         INVERTED_NORMAL_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, 0,                                                     ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_BLINK,                                          ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE,                                         ALTERNATE,         NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_TOP,                              ALTERNATE,         INVERTED_NORMAL_TOP)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BOTTOM,                           ALTERNATE,         INVERTED_NORMAL_BOTTOM)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_EDGES,                            ALTERNATE,         INVERTED_NORMAL_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK,                            ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               ALTERNATE,         INVERTED)

    #              cursor/phase        control register                                       attributes         result
    await sty_test(0,                  0,                                                     ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(0,                  CURSOR_BLINK,                                          ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE,                                         ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_TOP,                              ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BOTTOM,                           ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_EDGES,                            ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK,                            ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(0,                  CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        0,                                                     ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_BLINK,                                          ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE,                                         ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_TOP,                              ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BOTTOM,                           ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_EDGES,                            ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK,                            ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR,             0,                                                     ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR,             CURSOR_BLINK,                                          ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR,             CURSOR_ENABLE,                                         ALTERNATE|INVERSE, INVERTED)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_TOP,                              ALTERNATE|INVERSE, INVERTED_TOP)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BOTTOM,                           ALTERNATE|INVERSE, INVERTED_BOTTOM)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_EDGES,                            ALTERNATE|INVERSE, INVERTED_EDGES)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK,                            ALTERNATE|INVERSE, INVERTED)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 ALTERNATE|INVERSE, INVERTED_TOP)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              ALTERNATE|INVERSE, INVERTED_BOTTOM)
    await sty_test(CURSOR,             CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               ALTERNATE|INVERSE, INVERTED_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, 0,                                                     ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_BLINK,                                          ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE,                                         ALTERNATE|INVERSE, INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_TOP,                              ALTERNATE|INVERSE, INVERTED_TOP)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BOTTOM,                           ALTERNATE|INVERSE, INVERTED_BOTTOM)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_EDGES,                            ALTERNATE|INVERSE, INVERTED_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK,                            ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,                 ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM,              ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,               ALTERNATE|INVERSE, NO_CHANGE)

    #              cursor/phase        control register                                       attributes         result
    await sty_test(0,                  BLINK_ENABLE,                                          ALTERNATE,         NO_CHANGE)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_BLINK,                             ALTERNATE,         NO_CHANGE)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE,                            ALTERNATE,         NO_CHANGE)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_TOP,                 ALTERNATE,         NO_CHANGE)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BOTTOM,              ALTERNATE,         NO_CHANGE)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_EDGES,               ALTERNATE,         NO_CHANGE)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK,               ALTERNATE,         NO_CHANGE)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,    ALTERNATE,         NO_CHANGE)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM, ALTERNATE,         NO_CHANGE)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,  ALTERNATE,         NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE,                                          ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_BLINK,                             ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE,                            ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_TOP,                 ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BOTTOM,              ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_EDGES,               ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK,               ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,    ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM, ALTERNATE,         INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,  ALTERNATE,         INVERTED)
    await sty_test(CURSOR,             BLINK_ENABLE,                                          ALTERNATE,         NO_CHANGE)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_BLINK,                             ALTERNATE,         NO_CHANGE)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE,                            ALTERNATE,         INVERTED)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_TOP,                 ALTERNATE,         INVERTED_TOP)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BOTTOM,              ALTERNATE,         INVERTED_BOTTOM)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_EDGES,               ALTERNATE,         INVERTED_EDGES)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK,               ALTERNATE,         INVERTED)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,    ALTERNATE,         INVERTED_TOP)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM, ALTERNATE,         INVERTED_BOTTOM)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,  ALTERNATE,         INVERTED_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE,                                          ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_BLINK,                             ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE,                            ALTERNATE,         NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_TOP,                 ALTERNATE,         INVERTED_NORMAL_TOP)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BOTTOM,              ALTERNATE,         INVERTED_NORMAL_BOTTOM)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_EDGES,               ALTERNATE,         INVERTED_NORMAL_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK,               ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,    ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM, ALTERNATE,         INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,  ALTERNATE,         INVERTED)

    #              cursor/phase        control register                                       attributes         result
    await sty_test(0,                  BLINK_ENABLE,                                          ALTERNATE|INVERSE, INVERTED)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_BLINK,                             ALTERNATE|INVERSE, INVERTED)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE,                            ALTERNATE|INVERSE, INVERTED)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_TOP,                 ALTERNATE|INVERSE, INVERTED)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BOTTOM,              ALTERNATE|INVERSE, INVERTED)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_EDGES,               ALTERNATE|INVERSE, INVERTED)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK,               ALTERNATE|INVERSE, INVERTED)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,    ALTERNATE|INVERSE, INVERTED)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM, ALTERNATE|INVERSE, INVERTED)
    await sty_test(0,                  BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,  ALTERNATE|INVERSE, INVERTED)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE,                                          ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_BLINK,                             ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE,                            ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_TOP,                 ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BOTTOM,              ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_EDGES,               ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK,               ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,    ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM, ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(BLINK_PHASE,        BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,  ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR,             BLINK_ENABLE,                                          ALTERNATE|INVERSE, INVERTED)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_BLINK,                             ALTERNATE|INVERSE, INVERTED)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE,                            ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_TOP,                 ALTERNATE|INVERSE, INVERTED_NORMAL_TOP)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BOTTOM,              ALTERNATE|INVERSE, INVERTED_NORMAL_BOTTOM)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_EDGES,               ALTERNATE|INVERSE, INVERTED_NORMAL_EDGES)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK,               ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,    ALTERNATE|INVERSE, INVERTED_NORMAL_TOP)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM, ALTERNATE|INVERSE, INVERTED_NORMAL_BOTTOM)
    await sty_test(CURSOR,             BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,  ALTERNATE|INVERSE, INVERTED_NORMAL_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE,                                          ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_BLINK,                             ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE,                            ALTERNATE|INVERSE, INVERTED)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_TOP,                 ALTERNATE|INVERSE, INVERTED_TOP)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BOTTOM,              ALTERNATE|INVERSE, INVERTED_BOTTOM)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_EDGES,               ALTERNATE|INVERSE, INVERTED_EDGES)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK,               ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_TOP,    ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_BOTTOM, ALTERNATE|INVERSE, NO_CHANGE)
    await sty_test(CURSOR|BLINK_PHASE, BLINK_ENABLE|CURSOR_ENABLE|CURSOR_BLINK|CURSOR_EDGES,  ALTERNATE|INVERSE, NO_CHANGE)

    WHITE_SPACE = [
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
        0b0011111111110000, 0b0000000000000000,
        0b0011000000011000, 0b0000000000000000,
        0b0011000000001100, 0b0000000000000000,
        0b0011000000001100, 0b0000000000000000,
        0b0011000000001100, 0b0000000000000000,
        0b0011000000011000, 0b0000000000000000,
        0b0011111111110000, 0b0000000000000000,
        0b0011000011000000, 0b0000000000000000,
        0b0011000001100000, 0b0000000000000000,
        0b0011000000110000, 0b0000000000000000,
        0b0011000000011000, 0b0000000000000000,
        0b0011000000001100, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
        0b0000000000000000, 0b0000000000000000,
    ]

    FULL_BLOCK = [
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
        0b0011111111110000, 0b1111111111111111,
        0b0011000000011000, 0b1111111111111111,
        0b0011000000001100, 0b1111111111111111,
        0b0011000000001100, 0b1111111111111111,
        0b0011000000001100, 0b1111111111111111,
        0b0011000000011000, 0b1111111111111111,
        0b0011111111110000, 0b1111111111111111,
        0b0011000011000000, 0b1111111111111111,
        0b0011000001100000, 0b1111111111111111,
        0b0011000000110000, 0b1111111111111111,
        0b0011000000011000, 0b1111111111111111,
        0b0011000000001100, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
        0b0000000000000000, 0b1111111111111111,
    ]

    #              phase        ctrl          attributes                      result
    await sty_test(0,           0,            0,                              NO_CHANGE)
    await sty_test(BLINK_PHASE, 0,            0,                              NO_CHANGE)
    await sty_test(0,           0,            BLINK,                          NO_CHANGE)
    await sty_test(BLINK_PHASE, 0,            BLINK,                          NO_CHANGE)
    await sty_test(0,           0,                  ALTERNATE,                INVERTED)
    await sty_test(BLINK_PHASE, 0,                  ALTERNATE,                INVERTED)
    await sty_test(0,           0,            BLINK|ALTERNATE,                INVERTED)
    await sty_test(BLINK_PHASE, 0,            BLINK|ALTERNATE,                INVERTED)
    await sty_test(0,           0,                            INVERSE,        INVERTED)
    await sty_test(BLINK_PHASE, 0,                            INVERSE,        INVERTED)
    await sty_test(0,           0,            BLINK|          INVERSE,        INVERTED)
    await sty_test(BLINK_PHASE, 0,            BLINK|          INVERSE,        INVERTED)
    await sty_test(0,           0,                  ALTERNATE|INVERSE,        NO_CHANGE)
    await sty_test(BLINK_PHASE, 0,                  ALTERNATE|INVERSE,        NO_CHANGE)
    await sty_test(0,           0,            BLINK|ALTERNATE|INVERSE,        NO_CHANGE)
    await sty_test(BLINK_PHASE, 0,            BLINK|ALTERNATE|INVERSE,        NO_CHANGE)
    await sty_test(0,           0,                                    HIDDEN, WHITE_SPACE)
    await sty_test(BLINK_PHASE, 0,                                    HIDDEN, WHITE_SPACE)
    await sty_test(0,           0,            BLINK|                  HIDDEN, WHITE_SPACE)
    await sty_test(BLINK_PHASE, 0,            BLINK|                  HIDDEN, WHITE_SPACE)
    await sty_test(0,           0,                  ALTERNATE|        HIDDEN, FULL_BLOCK)
    await sty_test(BLINK_PHASE, 0,                  ALTERNATE|        HIDDEN, FULL_BLOCK)
    await sty_test(0,           0,            BLINK|ALTERNATE|        HIDDEN, FULL_BLOCK)
    await sty_test(BLINK_PHASE, 0,            BLINK|ALTERNATE|        HIDDEN, FULL_BLOCK)
    await sty_test(0,           0,                            INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(BLINK_PHASE, 0,                            INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(0,           0,            BLINK|          INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(BLINK_PHASE, 0,            BLINK|          INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(0,           0,                  ALTERNATE|INVERSE|HIDDEN, WHITE_SPACE)
    await sty_test(BLINK_PHASE, 0,                  ALTERNATE|INVERSE|HIDDEN, WHITE_SPACE)
    await sty_test(0,           0,            BLINK|ALTERNATE|INVERSE|HIDDEN, WHITE_SPACE)
    await sty_test(BLINK_PHASE, 0,            BLINK|ALTERNATE|INVERSE|HIDDEN, WHITE_SPACE)

    #              phase        ctrl          attributes                      result
    await sty_test(0,           CTRL_DEFAULT, 0,                              NO_CHANGE)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT, 0,                              NO_CHANGE)
    await sty_test(0,           CTRL_DEFAULT, BLINK,                          NO_CHANGE)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT, BLINK,                          WHITE_SPACE)
    await sty_test(0,           CTRL_DEFAULT,       ALTERNATE,                NO_CHANGE)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT,       ALTERNATE,                INVERTED)
    await sty_test(0,           CTRL_DEFAULT, BLINK|ALTERNATE,                NO_CHANGE)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT, BLINK|ALTERNATE,                FULL_BLOCK)
    await sty_test(0,           CTRL_DEFAULT,                 INVERSE,        INVERTED)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT,                 INVERSE,        INVERTED)
    await sty_test(0,           CTRL_DEFAULT, BLINK|          INVERSE,        INVERTED)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT, BLINK|          INVERSE,        FULL_BLOCK)
    await sty_test(0,           CTRL_DEFAULT,       ALTERNATE|INVERSE,        INVERTED)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT,       ALTERNATE|INVERSE,        NO_CHANGE)
    await sty_test(0,           CTRL_DEFAULT, BLINK|ALTERNATE|INVERSE,        INVERTED)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT, BLINK|ALTERNATE|INVERSE,        WHITE_SPACE)
    await sty_test(0,           CTRL_DEFAULT,                         HIDDEN, WHITE_SPACE)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT,                         HIDDEN, WHITE_SPACE)
    await sty_test(0,           CTRL_DEFAULT, BLINK|                  HIDDEN, WHITE_SPACE)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT, BLINK|                  HIDDEN, WHITE_SPACE)
    await sty_test(0,           CTRL_DEFAULT,       ALTERNATE|        HIDDEN, WHITE_SPACE)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT,       ALTERNATE|        HIDDEN, FULL_BLOCK)
    await sty_test(0,           CTRL_DEFAULT, BLINK|ALTERNATE|        HIDDEN, WHITE_SPACE)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT, BLINK|ALTERNATE|        HIDDEN, FULL_BLOCK)
    await sty_test(0,           CTRL_DEFAULT,                 INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT,                 INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(0,           CTRL_DEFAULT, BLINK|          INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT, BLINK|          INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(0,           CTRL_DEFAULT,       ALTERNATE|INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT,       ALTERNATE|INVERSE|HIDDEN, WHITE_SPACE)
    await sty_test(0,           CTRL_DEFAULT, BLINK|ALTERNATE|INVERSE|HIDDEN, FULL_BLOCK)
    await sty_test(BLINK_PHASE, CTRL_DEFAULT, BLINK|ALTERNATE|INVERSE|HIDDEN, WHITE_SPACE)

#include "module/module.hpp"

#include <gtest/gtest.h>

TEST(ModuleTest, ReturnsAnswer) {
    constexpr int expected_answer = 42;
    EXPECT_EQ(module::answer(), expected_answer);
}
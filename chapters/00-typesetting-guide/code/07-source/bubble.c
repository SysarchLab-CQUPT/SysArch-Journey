/* 冒泡排序：一段可以直接放进教材的短代码 */
#include <stdio.h>

void bubble_sort(int *a, int n)
{
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - 1 - i; j++) {
            if (a[j] > a[j + 1]) {      /* 交换相邻的两个元素 */
                int t = a[j];
                a[j] = a[j + 1];
                a[j + 1] = t;
            }
        }
    }
}

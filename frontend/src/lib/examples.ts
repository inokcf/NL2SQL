/**
 * 首页与侧边栏共用的示例问题
 */
import type { Component } from "vue";
import {
  BarChart3,
  Search,
  ShoppingBag,
  UserRound,
} from "lucide-vue-next";

export type ExamplePrompt = {
  text: string;
  label: string;
  icon: Component;
};

export const examplePrompts: ExamplePrompt[] = [
  {
    text: "统计 2025 年第一季度各大区的 GMV，并按 GMV 从高到低排序",
    label: "区域趋势",
    icon: BarChart3,
  },
  {
    text: "统计 2025 年 3 月各商品品类的销量和销售额",
    label: "品类分析",
    icon: ShoppingBag,
  },
  {
    text: "查询华东地区 2025 年第一季度销售额最高的前 5 个商品",
    label: "商品排行",
    icon: Search,
  },
  {
    text: "按会员等级统计 2025 年第一季度的订单数和销售额",
    label: "用户分层",
    icon: UserRound,
  },
];

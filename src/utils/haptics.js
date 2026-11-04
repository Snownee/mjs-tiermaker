/**
 * 触发震动反馈。
 * 浏览器要求页面已经获得用户激活（sticky activation），否则会静默拦截
 * 并打印 [Intervention] 提示。长按回调里调用时可能尚未发生 touchend，
 * 因此先判断激活状态，避免产生无意义的控制台警告。
 * @param {number} duration - 震动时长（毫秒）
 */
export const vibrate = (duration) => {
  if (navigator.userActivation?.hasBeenActive) {
    navigator.vibrate?.(duration);
  }
};

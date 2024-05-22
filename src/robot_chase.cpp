/*
robot_chase subscribe to /tf, or /tf_static topic
- timer callback group to publish to cmd_vel
- calculate tf parameters into Goal Position parameter.
- tf listener
*/
#include "geometry_msgs/msg/detail/point__struct.hpp"
#include "geometry_msgs/msg/detail/quaternion__struct.hpp"
#include "geometry_msgs/msg/twist.hpp"

#include "tf2/LinearMath/Matrix3x3.h"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2/LinearMath/Vector3.h"
#include "tf2/exceptions.h"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"
#include <cmath>
#include <geometry_msgs/msg/point.h>
#include <rclcpp/rclcpp.hpp>
using namespace std::chrono_literals;

/* TODO
- No need call back group. Only one callback which is timer callbasck
- TF listener act as a one line of code
# C++
          t = tf_buffer_->lookupTransform(
            toFrameRel, fromFrameRel,
            tf2::TimePointZero);

# python
          now = rclpy.time.Time()
          trans = self.tf_buffer.lookup_transform(
                origin_frame,
                dest_frame,
                now)
*/

class TF_to_Twist : public rclcpp::Node {
public:
  explicit TF_to_Twist (
      const rclcpp::NodeOptions &options = rclcpp::NodeOptions())
      : Node("tf_to_twist_node", options) {


    tf_buffer_ = std::make_unique<tf2_ros::Buffer>(this->get_clock());
    tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

    timer1_ = this->create_wall_timer(
        500ms, std::bind(&TF_to_Twist::timer1_callback, this));

    publisher_ =
        this->create_publisher<geometry_msgs::msg::Twist>("rick/cmd_vel", 10);
  }

private:

  rclcpp::TimerBase::SharedPtr timer1_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;

  std::shared_ptr<tf2_ros::TransformListener> tf_listener_{nullptr};
  std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
  std::string fromFrameRel = "morty/base_link";
  std::string toFrameRel = "rick/base_link";

  void timer1_callback() {
    RCLCPP_DEBUG(this->get_logger(), "Timer 1 Callback Start");

     geometry_msgs::msg::TransformStamped t;
    try {
          rclcpp::Time now = this->get_clock()->now();
          t = tf_buffer_->lookupTransform(
            toFrameRel, fromFrameRel,
            tf2::TimePointZero);//
        } catch (const tf2::TransformException & ex) {
          RCLCPP_INFO(
            this->get_logger(), "Could not transform %s to %s: %s",
            toFrameRel.c_str(), fromFrameRel.c_str(), ex.what());
          return;
        }
        geometry_msgs::msg::Twist ling;
        static const double scaleRotationRate = 0.4;
        ling.angular.x = 0;
        ling.angular.y = 0;
        ling.angular.z = scaleRotationRate * atan2(
          t.transform.translation.y,
          t.transform.translation.x);

        static const double scaleForwardSpeed = 0.2;
        ling.linear.x = scaleForwardSpeed * sqrt(
          pow(t.transform.translation.x, 2) +
          pow(t.transform.translation.y, 2));
        ling.linear.y = 0;

         this->move_robot(ling);
    RCLCPP_INFO(this->get_logger(), "linear x %f, angular z %f",ling.linear.x,ling.angular.z);
  }

  void move_robot(geometry_msgs::msg::Twist &msg) { publisher_->publish(msg); }
};

int main(int argc, char *argv[]) {
  rclcpp::init(argc, argv);

  std::shared_ptr<TF_to_Twist> tf_to_twist_node = std::make_shared<TF_to_Twist>();

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(tf_to_twist_node);
  executor.spin();

  rclcpp::shutdown();
  return 0;
}